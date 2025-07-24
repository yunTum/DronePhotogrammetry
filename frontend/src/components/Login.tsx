import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { LoginCredentials } from '../types';
import { Box, Button, Input, Heading, VStack, Text } from "@chakra-ui/react";

interface LoginProps {
  onGlbViewerClick: () => void;
}

const Login: React.FC<LoginProps> = ({ onGlbViewerClick }) => {
  const [credentials, setCredentials] = useState<LoginCredentials>({
    username: '',
    password: '',
  });
  const [error, setError] = useState<string | null>(null);
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    try {
      await login(credentials);
    } catch (err) {
      setError('ログインに失敗しました。ユーザー名とパスワードを確認してください。');
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setCredentials(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  return (
    <Box minH="100vh" bg="gray.900" display="flex" alignItems="center" justifyContent="center">
      <Box maxW="md" w="100%" mx="auto" p={8} borderRadius="lg" boxShadow="2xl" bg="gray.800">
        <Heading textAlign="center" mb={6} color="teal.200">WebODMログイン</Heading>
        <form onSubmit={handleSubmit}>
          {error && (
            <Text color="red.400" textAlign="center" mb={4}>
              {error}
            </Text>
          )}

          <VStack gap={4} align="stretch">
            <Box>
              <label htmlFor="username" style={{ color: '#e2e8f0' }}>ユーザー名</label>
              <Input
                id="username"
                name="username"
                value={credentials.username}
                onChange={handleChange}
                type="text"
                placeholder="ユーザー名を入力"
                required
                bg="gray.700"
                color="white"
                _placeholder={{ color: 'gray.400' }}
              />
            </Box>

            <Box>
              <label htmlFor="password" style={{ color: '#e2e8f0' }}>パスワード</label>
              <Input
                id="password"
                name="password"
                value={credentials.password}
                onChange={handleChange}
                type="password"
                placeholder="パスワードを入力"
                required
                bg="gray.700"
                color="white"
                _placeholder={{ color: 'gray.400' }}
              />
            </Box>

            <Button type="submit" colorScheme="teal" size="md" width="100%">
              ログイン
            </Button>
          </VStack>
        </form>
        
        <VStack gap={4} align="stretch" mt={6}>
          <Text textAlign="center" color="gray.400">
            ログインせずにGLBビューアを使用する
          </Text>
          <Button 
            onClick={onGlbViewerClick}
            colorScheme="green"
            size="md"
            width="100%"
            variant="outline"
            borderColor="green.400"
            color="green.200"
            _hover={{ bg: 'green.700', color: 'white' }}
          >
            GLBビューアを開く
          </Button>
        </VStack>
      </Box>
    </Box>
  );
};

export default Login; 