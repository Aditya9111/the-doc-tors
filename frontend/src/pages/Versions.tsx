import { useEffect, useState } from 'react'
import {
  Box,
  VStack,
  HStack,
  Heading,
  Text,
  Button,
  Icon,
  Spinner,
  Badge,
  Code,
  Flex,
  Grid
} from '@chakra-ui/react'
import { FiRefreshCw, FiFile, FiCode, FiCalendar, FiTrash2, FiX, FiCheckCircle, FiAlertCircle } from 'react-icons/fi'

export default function Versions() {
  const [versions, setVersions] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [deletingVersionId, setDeletingVersionId] = useState<string | null>(null)
  const [confirmDeleteVersion, setConfirmDeleteVersion] = useState<any>(null)
  const [isDeleteOpen, setIsDeleteOpen] = useState(false)

  const load = async () => {
    setLoading(true)
    setError(null)
    setSuccess(null)
    try {
      const res = await fetch('/api/versions')
      const json = await res.json()
      if (!res.ok) throw new Error(json.detail || res.statusText)
      setVersions(json.versions || [])
      setSuccess('Versions loaded successfully')
    } catch (e: any) { 
      setError(e.message)
    } finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  // Debug modal state
  useEffect(() => {
    console.log('Modal state changed:', { isDeleteOpen, confirmDeleteVersion })
  }, [isDeleteOpen, confirmDeleteVersion])

  const handleDeleteClick = (version: any) => {
    console.log('Delete clicked for version:', version)
    setConfirmDeleteVersion(version)
    setIsDeleteOpen(true)
  }

  const handleDeleteCancel = () => {
    setConfirmDeleteVersion(null)
    setIsDeleteOpen(false)
  }

  const handleDeleteConfirm = async () => {
    if (!confirmDeleteVersion) return
    
    console.log('Confirming delete for version:', confirmDeleteVersion)
    setDeletingVersionId(confirmDeleteVersion.version_id)
    setError(null)
    setSuccess(null)
    
    try {
      console.log('Making DELETE request to:', `/api/versions/${confirmDeleteVersion.version_id}`)
      const res = await fetch(`/api/versions/${confirmDeleteVersion.version_id}`, {
        method: 'DELETE'
      })
      const json = await res.json()
      
      console.log('Delete response:', res.status, json)
      
      if (!res.ok) {
        throw new Error(json.detail || 'Failed to delete version')
      }
      
      setSuccess(`Version "${confirmDeleteVersion.version_name}" deleted successfully`)
      setConfirmDeleteVersion(null)
      setIsDeleteOpen(false)
      
      // Refresh the versions list
      await load()
    } catch (e: any) {
      console.error('Delete error:', e)
      setError(`Failed to delete version: ${e.message}`)
    } finally {
      setDeletingVersionId(null)
    }
  }

  return (
    <VStack gap={8} align="stretch" className="animate-fade-in">
      <Box textAlign="center">
        <Heading size="2xl" color="gray.800" mb={2}>
          Versions
        </Heading>
        <Text color="gray.600" fontSize="lg">
          Manage and view all uploaded document versions
        </Text>
      </Box>

      {/* Header with Refresh Button */}
      <Flex justify="space-between" align="center">
        <Box />
        <Button
          onClick={load}
          disabled={loading}
          colorScheme="blue"
          variant="outline"
          className="hover-lift"
          leftIcon={loading ? <Spinner size="sm" /> : <Icon as={FiRefreshCw} />}
        >
          {loading ? 'Loading...' : 'Refresh'}
        </Button>
      </Flex>

      {/* Loading State */}
      {loading && (
        <Box className="glass-card" p={6}>
          <VStack gap={4}>
            <HStack gap={3}>
              <Spinner color="blue.400" />
              <Text color="gray.800" fontWeight="500">
                Loading versions...
              </Text>
            </HStack>
          </VStack>
        </Box>
      )}

      {/* Success Message */}
      {success && (
        <Box className="glass" p={4} borderRadius="12px" bg="green.500" color="white">
          <HStack gap={2}>
            <Icon as={FiCheckCircle} />
            <Text fontWeight="500">{success}</Text>
          </HStack>
        </Box>
      )}

      {/* Error Message */}
      {error && (
        <Box className="glass" p={4} borderRadius="12px" bg="red.500" color="white">
          <VStack gap={2} align="start">
            <HStack gap={2}>
              <Icon as={FiAlertCircle} />
              <Text fontWeight="500">Error</Text>
            </HStack>
            <Text fontSize="sm">{error}</Text>
          </VStack>
        </Box>
      )}

      {/* Empty State */}
      {versions.length === 0 && !loading && (
        <Box className="glass-card" p={8} textAlign="center">
          <VStack gap={4}>
            <Icon as={FiFile} boxSize={12} color="gray.400" />
            <VStack gap={2}>
              <Text color="gray.800" fontWeight="500" fontSize="lg">
                No versions found
              </Text>
              <Text color="gray.600">
                Upload some ZIP files first to see them here
              </Text>
            </VStack>
          </VStack>
        </Box>
      )}

      {/* Versions Grid */}
      {versions.length > 0 && (
        <Grid templateColumns={{ base: '1fr', md: 'repeat(2, 1fr)', lg: 'repeat(3, 1fr)' }} gap={6}>
          {versions.map(v => (
            <Box key={v.version_id} className="glass-card hover-lift" p={6}>
              <VStack gap={4} align="stretch">
                {/* Header */}
                <Flex justify="space-between" align="center">
                  <Heading size="md" color="gray.800">
                    {v.version_name}
                  </Heading>
                  <Badge
                    colorScheme={v.status === 'active' ? 'green' : 'gray'}
                    px={3}
                    py={1}
                    borderRadius="full"
                    fontSize="xs"
                    fontWeight="600"
                  >
                    {v.status}
                  </Badge>
                </Flex>

                {/* Version ID */}
                <Code colorScheme="blue" px={2} py={1} borderRadius="md" fontSize="xs">
                  {v.version_id}
                </Code>

                {/* Description */}
                <Text color="gray.600" fontSize="sm">
                  {v.description || 'No description provided'}
                </Text>

                {/* Stats */}
                <Grid templateColumns="1fr 1fr" gap={4}>
                  <Box>
                    <Text color="gray.500" fontSize="sm" mb={1}>
                      Files
                    </Text>
                    <Text color="blue.600" fontWeight="bold" fontSize="lg">
                      {v.file_count}
                    </Text>
                  </Box>
                  <Box>
                    <Text color="gray.500" fontSize="sm" mb={1}>
                      Chunks
                    </Text>
                    <Text color="blue.600" fontWeight="bold" fontSize="lg">
                      {v.chunk_count}
                    </Text>
                  </Box>
                </Grid>

                {/* File Types */}
                {v.file_types && v.file_types.length > 0 && (
                  <Box>
                    <Text color="gray.800" fontWeight="500" fontSize="sm" mb={2}>
                      File Types
                    </Text>
                    <HStack gap={2} wrap="wrap">
                      {v.file_types.map((type: string, i: number) => (
                        <Badge
                          key={i}
                          colorScheme="blue"
                          variant="subtle"
                          px={2}
                          py={1}
                          borderRadius="md"
                          fontSize="xs"
                        >
                          {type}
                        </Badge>
                      ))}
                    </HStack>
                  </Box>
                )}

                {/* Tags */}
                {v.tags && v.tags.length > 0 && (
                  <Box>
                    <Text color="gray.800" fontWeight="500" fontSize="sm" mb={2}>
                      Tags
                    </Text>
                    <HStack gap={2} wrap="wrap">
                      {v.tags.map((tag: string, i: number) => (
                        <Badge
                          key={i}
                          colorScheme="purple"
                          variant="subtle"
                          px={2}
                          py={1}
                          borderRadius="md"
                          fontSize="xs"
                        >
                          {tag}
                        </Badge>
                      ))}
                    </HStack>
                  </Box>
                )}

                {/* Upload Date */}
                <HStack gap={2} color="gray.500" fontSize="sm">
                  <Icon as={FiCalendar} />
                  <Text>
                    {new Date(v.upload_timestamp).toLocaleString()}
                  </Text>
                </HStack>

                {/* Delete Button */}
                <Button
                  onClick={() => handleDeleteClick(v)}
                  disabled={deletingVersionId === v.version_id}
                  colorScheme="red"
                  variant="outline"
                  size="sm"
                  className="hover-lift"
                >
                  <HStack gap={2}>
                    {deletingVersionId === v.version_id ? <Spinner size="sm" /> : <Icon as={FiTrash2} />}
                    <Text>{deletingVersionId === v.version_id ? 'Deleting...' : 'Delete Version'}</Text>
                  </HStack>
                </Button>
              </VStack>
            </Box>
          ))}
        </Grid>
      )}

      {/* Delete Confirmation Modal */}
      {isDeleteOpen && confirmDeleteVersion && (
        <Box
          position="fixed"
          top={0}
          left={0}
          right={0}
          bottom={0}
          bg="rgba(0, 0, 0, 0.5)"
          display="flex"
          alignItems="center"
          justifyContent="center"
          zIndex={1000}
        >
          <Box
            bg="white"
            p={6}
            maxW="400px"
            w="90%"
            borderRadius="16px"
            boxShadow="0 10px 25px rgba(0, 0, 0, 0.1)"
            border="1px solid"
            borderColor="gray.200"
          >
            <VStack gap={4} align="stretch">
              {/* Header */}
              <Flex justify="space-between" align="center">
                <Heading size="md" color="gray.800">
                  Delete Version?
                </Heading>
                <Button
                  onClick={handleDeleteCancel}
                  variant="ghost"
                  size="sm"
                  color="gray.500"
                >
                  <Icon as={FiX} />
                </Button>
              </Flex>

              {/* Content */}
              <VStack gap={3} align="stretch">
                <Text color="gray.600">
                  Are you sure you want to delete <strong>"{confirmDeleteVersion.version_name}"</strong>?
                </Text>
                <Text color="gray.500" fontSize="sm">
                  This will permanently delete:
                </Text>
                <Box as="ul" pl={5} color="gray.500" fontSize="sm">
                  <li>All embeddings and vectorstore</li>
                  <li>All metadata for this version</li>
                  <li>Cannot be undone</li>
                </Box>
              </VStack>

              {/* Actions */}
              <HStack gap={3} justify="flex-end">
                <Button
                  onClick={handleDeleteCancel}
                  disabled={deletingVersionId === confirmDeleteVersion.version_id}
                  variant="outline"
                  size="sm"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleDeleteConfirm}
                  disabled={deletingVersionId === confirmDeleteVersion.version_id}
                  colorScheme="red"
                  size="sm"
                >
                  <HStack gap={2}>
                    {deletingVersionId === confirmDeleteVersion.version_id ? <Spinner size="sm" /> : <Icon as={FiTrash2} />}
                    <Text>{deletingVersionId === confirmDeleteVersion.version_id ? 'Deleting...' : 'Delete Version'}</Text>
                  </HStack>
                </Button>
              </HStack>
            </VStack>
          </Box>
        </Box>
      )}
    </VStack>
  )
}