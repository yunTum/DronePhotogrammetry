import * as AdmZip from 'adm-zip';
import * as path from 'path';
import * as fs from 'fs';
import * as obj2gltf from 'obj2gltf';
import * as sharp from 'sharp';

/**
 * PNGファイルを圧縮する
 * @param inputPath 入力PNGファイルのパス
 * @param outputPath 出力PNGファイルのパス
 * @param options 圧縮オプション
 * @returns 圧縮後のファイルサイズ
 */
async function compressPng(
  inputPath: string, 
  outputPath: string, 
  options: {
    quality?: number;
    maxWidth?: number;
    maxHeight?: number;
    compressionLevel?: number;
  } = {}
): Promise<number> {
  const {
    quality = 80,
    maxWidth = 1024,
    maxHeight = 1024,
    compressionLevel = 9
  } = options;

  try {
    // 元のファイルサイズを取得
    const originalStats = fs.statSync(inputPath);
    const originalSize = originalStats.size;
    
    // 一時ファイル名を生成
    const tempOutputPath = outputPath + '.temp';

    // sharpで画像を処理（一時ファイルに出力）
    await sharp(inputPath)
      .resize(maxWidth, maxHeight, {
        fit: 'inside',
        withoutEnlargement: true
      })
      .png({
        quality: quality,
        compressionLevel: compressionLevel,
        adaptiveFiltering: true,
        force: true
      })
      .toFile(tempOutputPath);

    // 元のファイルを削除してから一時ファイルをリネーム
    fs.unlinkSync(inputPath);
    fs.renameSync(tempOutputPath, outputPath);

    // 圧縮後のファイルサイズを取得
    const compressedStats = fs.statSync(outputPath);
    const compressedSize = compressedStats.size;

    return compressedSize;
  } catch (error) {
    console.error(`PNG圧縮エラー (${inputPath}):`, error);
    // エラーの場合は元のファイルをそのまま使用
    return fs.statSync(inputPath).size;
  }
}

/**
 * ディレクトリ内の全PNGファイルを圧縮する
 * @param directoryPath 対象ディレクトリのパス
 * @param options 圧縮オプション
 * @returns 圧縮結果の統計
 */
async function compressAllPngsInDirectory(
  directoryPath: string,
  options: {
    quality?: number;
    maxWidth?: number;
    maxHeight?: number;
    compressionLevel?: number;
  } = {}
): Promise<{
  totalFiles: number;
  totalOriginalSize: number;
  totalCompressedSize: number;
  averageCompressionRatio: number;
}> {
  const pngFiles = fs.readdirSync(directoryPath)
    .filter(file => file.toLowerCase().endsWith('.png'))
    .map(file => path.join(directoryPath, file));

  if (pngFiles.length === 0) {
    console.log('圧縮対象のPNGファイルが見つかりません');
    return {
      totalFiles: 0,
      totalOriginalSize: 0,
      totalCompressedSize: 0,
      averageCompressionRatio: 0
    };
  }

  console.log(`${pngFiles.length}個のPNGファイルを圧縮開始...`);

  let totalOriginalSize = 0;
  let totalCompressedSize = 0;

  for (const pngFile of pngFiles) {
    const originalSize = fs.statSync(pngFile).size;
    totalOriginalSize += originalSize;

    // 同じファイルパスで圧縮（内部で一時ファイルを使用）
    const compressedSize = await compressPng(pngFile, pngFile, options);
    totalCompressedSize += compressedSize;
  }

  const averageCompressionRatio = ((totalOriginalSize - totalCompressedSize) / totalOriginalSize * 100);
  
  console.log(`PNG圧縮完了: ${pngFiles.length}ファイル - 合計${(totalOriginalSize / 1024 / 1024).toFixed(1)}MB → ${(totalCompressedSize / 1024 / 1024).toFixed(1)}MB (${averageCompressionRatio.toFixed(1)}%削減)`);

  return {
    totalFiles: pngFiles.length,
    totalOriginalSize,
    totalCompressedSize,
    averageCompressionRatio
  };
}

/**
 * zipバッファからGLBファイル（glTFバイナリ）を生成
 * @param zipBuffer zipファイルのバッファ
 * @returns GLBファイルのバッファ
 */
export async function convertZipToGlb(zipBuffer: Buffer): Promise<Buffer> {
  console.log('開始: zipファイルの解析');
  const zip = new AdmZip(zipBuffer);
  const entries = zip.getEntries();

  // OBJ、MTL、テクスチャファイルを探す
  const objEntry = entries.find(e => e.entryName.endsWith('.obj'));
  const mtlEntry = entries.find(e => e.entryName.endsWith('odm_textured_model_geo.mtl'));
  const textureEntries = entries.filter(e => 
    e.entryName.endsWith('.png') || 
    e.entryName.endsWith('.jpg') || 
    e.entryName.endsWith('.jpeg')
  );
  
  console.log(`見つかったファイル: OBJ=${!!objEntry}, MTL=${!!mtlEntry}, テクスチャ=${textureEntries.length}個`);

  if (!objEntry) {
    throw new Error('OBJファイルが見つかりません');
  }

  // 一時ディレクトリを作成
  const tmpDir = path.join(__dirname, '..', 'tmp', `gltf-convert-${Date.now()}`);
  if (!fs.existsSync(tmpDir)) {
    fs.mkdirSync(tmpDir, { recursive: true });
  }
  console.log(`一時ディレクトリ作成: ${tmpDir}`);

  try {
    // OBJファイルの内容を読み込んで、MTLファイル参照を修正
    let objContent = objEntry.getData().toString('utf8');
    const objFileName = path.basename(objEntry.entryName);
    const objPath = path.join(tmpDir, objFileName);
    
    // MTLファイルを保存（存在する場合）
    if (mtlEntry) {
      const mtlFileName = path.basename(mtlEntry.entryName);
      const mtlPath = path.join(tmpDir, mtlFileName);
      fs.writeFileSync(mtlPath, mtlEntry.getData());
      
      // OBJファイル内のmtllib行を修正
      objContent = objContent.replace(
        /^mtllib\s+.*$/gm,
        `mtllib ${mtlFileName}`
      );
    }
      
    // 修正されたOBJファイルを保存
    fs.writeFileSync(objPath, objContent);

    // テクスチャファイルを保存（全て）
    for (const textureEntry of textureEntries) {
      const textureFileName = path.basename(textureEntry.entryName);
      const texturePath = path.join(tmpDir, textureFileName);
      try {
        fs.writeFileSync(texturePath, textureEntry.getData());
        // Check if the file exists after saving
        if (!fs.existsSync(texturePath)) {
        }
      } catch (error) {
        console.error(`テクスチャファイルの保存エラー: ${texturePath}`, error);
      }
    }

    // PNGファイルを圧縮（前処理）
    if (textureEntries.length > 0) {
      console.log('PNGファイルの圧縮を開始...');
      const compressionOptions = {
        quality: 80,        // 品質（0-100）
        maxWidth: 1024,     // 最大幅
        maxHeight: 1024,    // 最大高さ
        compressionLevel: 9 // PNG圧縮レベル（0-9）
      };
      
      const compressionResult = await compressAllPngsInDirectory(tmpDir, compressionOptions);
      console.log(`PNG圧縮結果: ${compressionResult.totalFiles}ファイル, ${compressionResult.averageCompressionRatio.toFixed(1)}%削減`);
    }

    // obj2gltfでGLBファイルを生成
    console.log('obj2gltfでGLB変換開始...');
    const options = {
      binary: true, // GLB形式で出力
      checkTransparency: false,
      secure: false,
      separate: false,
      separateTextures: false,
      optimizeForCesium: false,
      upAxis: 'Y'
    };
    
    try {
      const glbBuffer = await obj2gltf(objPath, options);
      console.log(`GLB変換完了: ${glbBuffer.length.toLocaleString()} bytes`);
      
      // デバッグ用にGLBファイルを一時ディレクトリに保存
      const debugPath = path.join(tmpDir, 'debug_result.glb');
      fs.writeFileSync(debugPath, glbBuffer);
      console.log(`デバッグ: GLBファイルを保存しました: ${debugPath} (${glbBuffer.length} bytes)`);
      
      return glbBuffer;
      } catch (error) {
      console.error('obj2gltf変換エラー:', error);
      throw error;
    }

  } finally {
    // 一時ディレクトリを削除
    // try {
    //   fs.rmSync(tmpDir, { recursive: true, force: true });
    //   console.log(`一時ディレクトリ削除: ${tmpDir}`);
    // } catch (error) {
    //   console.warn('一時ディレクトリの削除に失敗:', error);
    // }
  }
}
