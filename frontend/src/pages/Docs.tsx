import { useState } from 'react'
import {
  Box,
  VStack,
  HStack,
  Heading,
  Text,
  Button,
  Input,
  Icon,
  Spinner,
  Badge,
  Code,
  Flex
} from '@chakra-ui/react'
import { FiFileText, FiFile, FiCheckCircle, FiDownload, FiUpload, FiX, FiAlertCircle } from 'react-icons/fi'

// Helper function to format file size
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

export default function Docs() {
  const [file, setFile] = useState<File | null>(null)
  const [saveAsFiles, setSaveAsFiles] = useState(true)
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [downloading, setDownloading] = useState(false)
  const [downloadingFile, setDownloadingFile] = useState<string | null>(null)
  const [uploadProgress, setUploadProgress] = useState<{
    total: number
    completed: number
    status: string
  } | null>(null)

  const submit = async () => {
    if (!file) return
    setLoading(true)
    setError(null)
    setSuccess(null)
    setResult(null)
    setUploadProgress(null)
    
    const form = new FormData()
    form.append('file', file)
    form.append('save_as_files', String(saveAsFiles))
    
    try {
      const res = await fetch('/api/generate_documentation', { method: 'POST', body: form })
      const json = await res.json()
      if (!res.ok) throw new Error(json.detail || res.statusText)
      
      if (json.job_id) {
        // Start progress tracking
        setUploadProgress({
          total: json.total_files,
          completed: 0,
          status: 'processing'
        })
        
        pollProgress(json.job_id)
      } else {
        // Fallback for old API response
        setResult(json)
        setSuccess('Documentation generated!')
        setLoading(false)
      }
    } catch (e: any) { 
      setError(e.message)
      setLoading(false)
    }
  }

  const pollProgress = async (jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/documentation_progress/${jobId}`)
        const progress = await res.json()
        
        setUploadProgress({
          total: progress.total_files,
          completed: progress.completed_files,
          status: progress.status
        })
        
        if (progress.status === 'completed') {
          clearInterval(interval)
          setResult(progress.result)
          setSuccess('Documentation generated!')
          setUploadProgress(null)
          setLoading(false)
        } else if (progress.status === 'error') {
          clearInterval(interval)
          setError(progress.error || 'Documentation generation failed')
          setUploadProgress(null)
          setLoading(false)
        }
      } catch (e) {
        clearInterval(interval)
        setError('Failed to fetch progress')
        setUploadProgress(null)
        setLoading(false)
      }
    }, 1000)  // Poll every second
  }

  const downloadDocs = async (downloadId: string) => {
    if (!downloadId) return
    setDownloading(true)
    setError(null)
    
    try {
      const response = await fetch(`/api/download_documentation/${downloadId}`)
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Download failed')
      }
      
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `documentation_${downloadId}.zip`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
      
      setSuccess('Documentation downloaded successfully!')
    } catch (e: any) {
      setError(`Download failed: ${e.message}`)
    } finally {
      setDownloading(false)
    }
  }

  const downloadSingleFile = async (downloadId: string, filename: string) => {
    if (!downloadId || !filename) return
    setDownloadingFile(filename)
    setError(null)
    
    try {
      const response = await fetch(`/api/download_documentation_file/${downloadId}/${filename}`)
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Download failed')
      }
      
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
      
      setSuccess(`${filename} downloaded successfully!`)
    } catch (e: any) {
      setError(`Download failed: ${e.message}`)
    } finally {
      setDownloadingFile(null)
    }
  }

  return (
    <VStack gap={8} align="stretch" className="animate-fade-in">
      <Box textAlign="center">
        <Heading size="2xl" color="gray.800" mb={2}>
          Generate Documentation
        </Heading>
        <Text color="gray.600" fontSize="lg">
          Create comprehensive documentation from your ZIP files
        </Text>
      </Box>
      
      {/* Upload Card */}
      <Box className="glass-card" p={8}>
        <VStack gap={6} align="stretch">
          <Box>
            <Heading size="lg" mb={2} color="gray.800">
              Upload ZIP for Documentation
            </Heading>
            <Text color="gray.600">
              Generate comprehensive documentation from your code files
            </Text>
          </Box>

          <VStack gap={4} align="stretch">
            <Box>
              <Text color="gray.800" fontWeight="500" mb={2}>Select ZIP File</Text>
              <Input
                type="file"
                accept=".zip"
                onChange={e => setFile(e.target.files?.[0] || null)}
                variant="outline"
                color="gray.800"
                _placeholder={{ color: 'gray.500' }}
              />
            </Box>
            
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

            <HStack gap={2}>
              <input
                type="checkbox"
                checked={saveAsFiles}
                onChange={e => setSaveAsFiles(e.target.checked)}
                style={{ cursor: 'pointer' }}
              />
              <Text color="gray.800" cursor="pointer" onClick={() => setSaveAsFiles(!saveAsFiles)}>
                Save as Markdown files
              </Text>
            </HStack>

            <Button
              onClick={submit}
              disabled={!file || loading}
              colorScheme="blue"
              size="lg"
              className="hover-lift"
            >
              <HStack gap={2}>
                {loading ? <Spinner size="sm" /> : <Icon as={FiFileText} />}
                <Text>{loading ? 'Generating...' : 'Generate Documentation'}</Text>
              </HStack>
            </Button>
          </VStack>
        </VStack>
      </Box>

      {/* Loading State */}
      {loading && !uploadProgress && (
        <Box className="glass-card" p={6}>
          <VStack gap={4}>
            <HStack gap={3}>
              <Spinner color="blue.400" />
              <Text color="gray.800" fontWeight="500">
                Generating documentation...
              </Text>
            </HStack>
            <Box w="100%" h="2px" className="glass" borderRadius="full" overflow="hidden">
              <Box w="100%" h="100%" bg="blue.400" className="animate-pulse" />
            </Box>
          </VStack>
        </Box>
      )}

      {/* Upload Progress */}
      {uploadProgress && (
        <Box className="glass-card" p={6}>
          <VStack gap={4} align="stretch">
            <HStack gap={3}>
              <Spinner color="blue.400" />
              <Heading size="md" color="gray.800">
                Generating Documentation...
              </Heading>
            </HStack>
            
            <Box>
              <Flex justify="space-between" mb={2}>
                <Text color="gray.600" fontSize="sm">Progress</Text>
                <Text color="gray.600" fontSize="sm">
                  {uploadProgress.completed} / {uploadProgress.total} files
                </Text>
              </Flex>
              
              <Box
                w="100%"
                h="24px"
                bg="gray.200"
                borderRadius="12px"
                overflow="hidden"
              >
                <Box
                  w={`${(uploadProgress.completed / uploadProgress.total) * 100}%`}
                  h="100%"
                  bg="blue.400"
                  transition="width 0.3s ease"
                  display="flex"
                  alignItems="center"
                  justifyContent="center"
                  color="white"
                  fontSize="12px"
                  fontWeight="bold"
                >
                  {Math.round((uploadProgress.completed / uploadProgress.total) * 100)}%
                </Box>
              </Box>
            </Box>
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
              <Text fontWeight="500">Generation Error</Text>
            </HStack>
            <Text fontSize="sm">{error}</Text>
          </VStack>
        </Box>
      )}

      {/* Results */}
      {result && (
        <Box className="glass-card" p={6}>
          <VStack gap={6} align="stretch">
            <HStack gap={3}>
              <Icon as={FiCheckCircle} color="green.400" boxSize={6} />
              <Heading size="md" color="green.600">
                Documentation Generated!
              </Heading>
            </HStack>

            <VStack gap={4} align="stretch">
              <HStack justify="space-between">
                <Text color="gray.800" fontWeight="500">Files Processed:</Text>
                <Badge colorScheme="blue" px={3} py={1} borderRadius="full">
                  {result.files_processed}
                </Badge>
              </HStack>
              <HStack justify="space-between">
                <Text color="gray.800" fontWeight="500">Successful:</Text>
                <Badge colorScheme="green" px={3} py={1} borderRadius="full">
                  {result.successful_documentations}
                </Badge>
              </HStack>
              <HStack justify="space-between">
                <Text color="gray.800" fontWeight="500">Failed:</Text>
                <Badge colorScheme="red" px={3} py={1} borderRadius="full">
                  {result.failed_documentations}
                </Badge>
              </HStack>
              <HStack justify="space-between">
                <Text color="gray.800" fontWeight="500">Skipped:</Text>
                <Badge colorScheme="gray" px={3} py={1} borderRadius="full">
                  {result.skipped_files}
                </Badge>
              </HStack>

              {result.output_directory && (
                <Box>
                  <Text color="gray.800" fontWeight="500" mb={2}>Output Directory:</Text>
                  <Code
                    display="block"
                    p={2}
                    bg="gray.100"
                    borderRadius="md"
                    fontSize="sm"
                    fontFamily="monospace"
                  >
                    {result.output_directory}
                  </Code>
                </Box>
              )}

              {result.individual_files && result.individual_files.length > 0 && (
                <Box>
                  <Text color="gray.800" fontWeight="500" mb={3}>Generated Files:</Text>
                  <VStack gap={2} align="stretch">
                    {result.individual_files.map((file: any, i: number) => (
                      <Box
                        key={i}
                        className="glass hover-lift"
                        p={3}
                        borderRadius="8px"
                      >
                        <HStack justify="space-between" align="center">
                          <HStack gap={3} flex={1}>
                            <Icon as={FiCheckCircle} color="green.400" boxSize={4} />
                            <VStack align="start" gap={1} flex={1}>
                              <Text
                                color="gray.800"
                                fontWeight="500"
                                fontSize="sm"
                                fontFamily="monospace"
                              >
                                {file.filename}
                              </Text>
                              <Text color="gray.600" fontSize="xs">
                                ({file.original_file})
                              </Text>
                            </VStack>
                          </HStack>
                          <Button
                            onClick={() => downloadSingleFile(result.download_id, file.filename)}
                            disabled={downloadingFile === file.filename}
                            size="sm"
                            colorScheme="blue"
                            variant="outline"
                          >
                            <HStack gap={1}>
                              {downloadingFile === file.filename ? (
                                <Spinner size="xs" />
                              ) : (
                                <Icon as={FiDownload} boxSize={3} />
                              )}
                              <Text fontSize="xs">
                                {downloadingFile === file.filename ? 'Downloading...' : 'Download'}
                              </Text>
                            </HStack>
                          </Button>
                        </HStack>
                      </Box>
                    ))}
                  </VStack>
                </Box>
              )}


              {result.download_id && (
                <Box mt={4}>
                  <HStack gap={3} mb={3}>
                    <Box h="1px" bg="gray.200" flex={1} />
                    <Text color="gray.600" fontSize="sm" fontWeight="500">OR</Text>
                    <Box h="1px" bg="gray.200" flex={1} />
                  </HStack>
                  <Button
                    onClick={() => downloadDocs(result.download_id)}
                    disabled={downloading}
                    colorScheme="green"
                    size="lg"
                    className="hover-lift"
                  >
                    <HStack gap={2}>
                      {downloading ? <Spinner size="sm" /> : <Icon as={FiDownload} />}
                      <Text>{downloading ? 'Preparing Download...' : 'Download All as ZIP'}</Text>
                    </HStack>
                  </Button>
                  {downloading && (
                    <Text mt={2} fontSize="sm" color="gray.600">
                      Creating ZIP file and preparing download...
                    </Text>
                  )}
                </Box>
              )}

              <Box h="1px" bg="gray.200" w="100%" />

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
          </VStack>
        </Box>
      )}
    </VStack>
  )
}


