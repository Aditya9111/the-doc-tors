import { Link, Outlet, useLocation } from 'react-router-dom'
import {
  Box,
  Container,
  Heading,
  HStack,
  Link as ChakraLink,
  VStack,
  Icon,
  Text,
  Flex
} from '@chakra-ui/react'
import { FiUpload, FiSearch, FiList, FiGitMerge, FiFileText, FiActivity } from 'react-icons/fi'

export default function App() {
  const { pathname } = useLocation()
  const isActive = (p: string) => pathname === p
  
  const navItems = [
    { path: '/upload', label: 'Upload', icon: FiUpload },
    { path: '/query', label: 'Query', icon: FiSearch },
    { path: '/versions', label: 'Versions', icon: FiList },
    { path: '/compare', label: 'Compare', icon: FiGitMerge },
    { path: '/docs', label: 'Docs', icon: FiFileText },
    { path: '/health', label: 'Health', icon: FiActivity },
  ]

  return (
    <Box minH="100vh" position="relative" className="animate-fade-in">
      {/* Animated background */}
      <Box
        position="fixed"
        top={0}
        left={0}
        right={0}
        bottom={0}
        zIndex={-1}
        className="animate-gradient"
        style={{
          background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 50%, #cbd5e1 100%)',
          backgroundSize: '400% 400%'
        }}
      />
      
      {/* Floating elements */}
      <Box
        position="fixed"
        top="10%"
        left="10%"
        w="200px"
        h="200px"
        borderRadius="50%"
        background="rgba(255, 255, 255, 0.3)"
        className="animate-float"
        zIndex={-1}
      />
      <Box
        position="fixed"
        top="60%"
        right="15%"
        w="150px"
        h="150px"
        borderRadius="50%"
        background="rgba(255, 255, 255, 0.2)"
        className="animate-float"
        style={{ animationDelay: '2s' }}
        zIndex={-1}
      />

      {/* Glass navigation bar */}
      <Box
        position="sticky"
        top={0}
        zIndex={1000}
        className="glass-strong"
        borderBottom="1px solid rgba(255, 255, 255, 0.1)"
        backdropFilter="blur(20px)"
      >
        <Container maxW="container.xl" py={4}>
          <Flex align="center" justify="space-between">
            <Heading 
              as="h1" 
              size="xl" 
              color="gray.800"
              fontWeight="700"
            >
              AskMe
            </Heading>
            
            <HStack gap={2}>
              {navItems.map(({ path, label, icon: IconComponent }) => (
                <Link key={path} to={path} style={{ textDecoration: 'none' }}>
                  <Box
                    px={4}
                    py={2}
                    borderRadius="12px"
                    className={`hover-lift ${isActive(path) ? 'glass-strong' : 'glass'}`}
                    color={isActive(path) ? 'gray.800' : 'gray.600'}
                    _hover={{
                      color: 'gray.800',
                      background: 'rgba(0, 0, 0, 0.05)'
                    }}
                    transition="all 0.3s ease"
                    display="flex"
                    alignItems="center"
                    gap={2}
                    fontWeight={isActive(path) ? '600' : '500'}
                  >
                    <Icon as={IconComponent} boxSize={4} />
                    <Text fontSize="sm" display={{ base: 'none', md: 'block' }}>
                      {label}
                    </Text>
                  </Box>
                </Link>
              ))}
              
            </HStack>
          </Flex>
        </Container>
      </Box>
      
      {/* Main content */}
      <Container maxW="container.xl" py={8}>
        <Box className="animate-slide-up">
          <Outlet />
        </Box>
      </Container>
    </Box>
  )
}


