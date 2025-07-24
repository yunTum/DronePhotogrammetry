import React from 'react';
import { Box, Button, Heading } from '@chakra-ui/react';

interface HeaderProps {
  title: string;
  leftButtonText?: string;
  onLeftButtonClick?: () => void;
  rightButtonText?: string;
  onRightButtonClick?: () => void;
  leftButtonColor?: string;
  rightButtonColor?: string;
}

const Header: React.FC<HeaderProps> = ({
  title,
  leftButtonText,
  onLeftButtonClick,
  rightButtonText,
  onRightButtonClick,
  leftButtonColor = '#319795',
  rightButtonColor = '#dc3545',
}) => (
  <Box className="App-header" position="relative" bg="gray.900" py={4} borderTopRadius="xl" boxShadow="md">
    {leftButtonText && (
      <Button
        onClick={onLeftButtonClick}
        style={{
          position: 'absolute',
          top: '1rem',
          left: '1rem',
          padding: '0.5rem 1rem',
          backgroundColor: leftButtonColor,
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer',
          fontSize: '0.9rem'
        }}
        _hover={{ bg: leftButtonColor === '#319795' ? '#2c7a7b' : leftButtonColor }}
      >
        {leftButtonText}
      </Button>
    )}
    <Heading color="teal.200" textAlign="center">{title}</Heading>
    {rightButtonText && (
      <Button
        onClick={onRightButtonClick}
        style={{
          position: 'absolute',
          top: '1rem',
          right: '1rem',
          padding: '0.5rem 1rem',
          backgroundColor: rightButtonColor,
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer',
          fontSize: '0.9rem'
        }}
        _hover={{ bg: rightButtonColor === '#dc3545' ? '#c82333' : rightButtonColor }}
      >
        {rightButtonText}
      </Button>
    )}
  </Box>
);

export default Header; 