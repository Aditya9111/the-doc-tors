import { useState, useRef } from 'react'
import {
  Box,
  VStack,
  HStack,
  Heading,
  Text,
  Button,
  Input,
  Textarea,
  Code,
  Icon,
  Spinner
} from '@chakra-ui/react'
import { FiUpload, FiFile, FiCheck, FiX, FiAlertCircle } from 'react-icons/fi'

// Helper function to format file size
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

export default function Upload() {
  const [file, setFile] = useState<File | null>(null)
  const [versionName, setVersionName] = useState('')
  const [description, setDescription] = useState('')
  const [tags, setTags] = useState('')
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0]
      if (droppedFile.name.endsWith('.zip')) {
        setFile(droppedFile)
      } else {
        setError("Please upload a ZIP file")
      }
    }
  }

  const upload = async () => {
    if (!file) return
    setLoading(true)
    setError(null)
    setSuccess(null)
    setResult(null)
    const form = new FormData()
    form.append('file', file)
    form.append('version_name', versionName || 'v' + new Date().toISOString().slice(0,19).replace(/[:T]/g,'-'))
    form.append('description', description)
    form.append('tags', tags)
    try {
      const res = await fetch('/api/ingest_versioned', { method: 'POST', body: form })
      const json = await res.json()
      if (!res.ok) throw new Error(json.detail || res.statusText)
      setResult(json)
      setSuccess('Upload successful!')
    } catch (e: any) {
      setError(e.message)
    } finally { setLoading(false) }
  }

  return (
    <VStack gap={8} align="stretch" className="animate-fade-in">
      <Box textAlign="center">
            <Heading size="2xl" color="gray.800" mb={2}>
              Upload ZIP Files
            </Heading>
            <Text color="gray.600" fontSize="lg">
              Process and analyze your documents with AI-powered insights
            </Text>
      </Box>

      {/* Upload Card */}
      <Box className="glass-card" p={8}>
        <VStack gap={6} align="stretch">
          <Box>
            <Heading size="lg" mb={2} color="gray.800">
              Upload New Version
            </Heading>
            <Text color="gray.600">
              Create a new version with metadata and AI processing
            </Text>
          </Box>

          {/* Drag and Drop Area */}
          <Box>
            <Text color="gray.800" fontWeight="500" mb={2}>Select ZIP File</Text>
            <Box
              ref={fileInputRef}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`glass ${dragActive ? 'glass-strong' : ''}`}
              border="2px dashed"
              borderColor={dragActive ? 'blue.400' : 'rgba(255, 255, 255, 0.3)'}
              borderRadius="16px"
              p={8}
              textAlign="center"
              cursor="pointer"
              transition="all 0.3s ease"
              _hover={{
                borderColor: 'blue.400',
                background: 'rgba(255, 255, 255, 0.15)'
              }}
            >
              <VStack gap={4}>
                <Icon as={FiUpload} boxSize={8} color="blue.400" />
                <VStack gap={2}>
                    <Text color="gray.800" fontWeight="500">
                      {dragActive ? 'Drop your ZIP file here' : 'Click to upload or drag and drop'}
                    </Text>
                    <Text color="gray.600" fontSize="sm">
                      Supports ZIP files up to 100MB
                    </Text>
                </VStack>
              </VStack>
            </Box>
            <Input
              ref={fileInputRef}
              type="file"
              accept=".zip"
              onChange={e => setFile(e.target.files?.[0] || null)}
              display="none"
            />
          </Box>

          {/* File Preview */}
          {file && (
            <Box className="glass" p={4} borderRadius="12px">
              <HStack gap={3}>
                <Icon as={FiFile} color="blue.400" />
                <VStack align="start" gap={1} flex={1}>
                    <Text color="gray.800" fontWeight="500" fontSize="sm">
                      {file.name}
                    </Text>
                    <Text color="gray.600" fontSize="xs">
                      {formatFileSize(file.size)}
                    </Text>
                </VStack>
                <Button
                  size="sm"
                  variant="ghost"
                  color="red.400"
                  onClick={() => setFile(null)}
                  _hover={{ background: 'rgba(255, 0, 0, 0.1)' }}
                >
                  <Icon as={FiX} />
                </Button>
              </HStack>
            </Box>
          )}

          {/* Form Fields */}
          <HStack gap={4} align="start">
            <Box flex={1}>
              <Text color="gray.800" fontWeight="500" mb={2}>Version Name</Text>
              <Input
                placeholder="e.g., v1.0.0"
                value={versionName}
                onChange={e => setVersionName(e.target.value)}
                variant="outline"
                color="gray.800"
                _placeholder={{ color: 'gray.500' }}
              />
            </Box>
            <Box flex={1}>
              <Text color="gray.800" fontWeight="500" mb={2}>Tags (comma-separated)</Text>
              <Input
                placeholder="e.g., release, stable"
                value={tags}
                onChange={e => setTags(e.target.value)}
                variant="outline"
                color="gray.800"
                _placeholder={{ color: 'gray.500' }}
              />
            </Box>
          </HStack>

          <Box>
            <Text color="gray.800" fontWeight="500" mb={2}>Description</Text>
            <Textarea
              placeholder="Describe what's in this version..."
              value={description}
              onChange={e => setDescription(e.target.value)}
              rows={3}
              variant="outline"
              color="gray.800"
              _placeholder={{ color: 'gray.500' }}
            />
          </Box>

          <Button
            onClick={upload}
            disabled={!file || loading}
            colorScheme="blue"
            size="lg"
            className="hover-lift"
          >
            <HStack gap={2}>
              {loading ? <Spinner size="sm" /> : <Icon as={FiUpload} />}
              <Text>{loading ? 'Processing...' : 'Upload as New Version'}</Text>
            </HStack>
          </Button>
        </VStack>
      </Box>

      {/* Loading State */}
      {loading && (
        <Box className="glass-card" p={6}>
          <VStack gap={4}>
            <HStack gap={3}>
              <Spinner color="blue.400" />
                  <Text color="gray.800" fontWeight="500">
                    Uploading and processing your files...
                  </Text>
            </HStack>
            <Box w="100%" h="2px" className="glass" borderRadius="full" overflow="hidden">
              <Box w="100%" h="100%" bg="blue.400" className="animate-pulse" />
            </Box>
          </VStack>
        </Box>
      )}

      {/* Success Message */}
      {success && (
        <Box className="glass" p={4} borderRadius="12px" bg="green.500" color="white">
          <HStack gap={2}>
            <Icon as={FiCheck} />
                  <Text fontWeight="500" color="white">{success}</Text>
          </HStack>
        </Box>
      )}

      {/* Error Message */}
      {error && (
        <Box className="glass" p={4} borderRadius="12px" bg="red.500" color="white">
          <VStack gap={2} align="start">
            <HStack gap={2}>
              <Icon as={FiAlertCircle} />
                <Text fontWeight="500" color="white">Upload Error</Text>
              </HStack>
              <Text fontSize="sm" color="white">{error}</Text>
          </VStack>
        </Box>
      )}

      {/* Results */}
      {result && (
        <Box className="glass-card" p={6}>
          <VStack gap={6} align="stretch">
            <HStack gap={3}>
              <Icon as={FiCheck} color="green.400" boxSize={6} />
                  <Heading size="md" color="green.600">
                    Upload Successful!
                  </Heading>
            </HStack>

            <VStack gap={4} align="stretch">
              <HStack justify="space-between">
                <Text color="gray.800" fontWeight="500">Files Processed:</Text>
                <Text color="blue.600" fontWeight="600">{result.files_processed}</Text>
              </HStack>
              <HStack justify="space-between">
                <Text color="gray.800" fontWeight="500">Chunks Created:</Text>
                <Text color="blue.600" fontWeight="600">{result.chunks_created}</Text>
              </HStack>
              {result.version_id && (
                <HStack justify="space-between">
                  <Text color="gray.800" fontWeight="500">Version ID:</Text>
                  <Code colorScheme="blue" px={2} py={1} borderRadius="md">
                    {result.version_id}
                  </Code>
                </HStack>
              )}
            </VStack>

            <Box h="1px" bg="rgba(255, 255, 255, 0.2)" w="100%" />

            <Box>
              <Text color="gray.800" fontWeight="500" mb={3}>Full Response:</Text>
              <Box
                className="glass"
                p={4}
                borderRadius="8px"
                overflow="auto"
                maxH="300px"
              >
                <Code
                  as="pre"
                  colorScheme="gray"
                  fontSize="xs"
                  whiteSpace="pre-wrap"
                  display="block"
                >
                  {JSON.stringify(result, null, 2)}
                </Code>
              </Box>
            </Box>
          </VStack>
        </Box>
      )}
    </VStack>
  )
}


