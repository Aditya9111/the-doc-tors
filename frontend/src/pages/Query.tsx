import { useState, useEffect, useRef } from 'react'
import {
  Box,
  Button,
  Heading,
  Input,
  Textarea,
  Text,
  VStack,
  HStack,
  Badge,
  Icon,
  Spinner,
  Code,
  useDisclosure
} from '@chakra-ui/react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { FiSearch, FiFile, FiCode, FiX, FiChevronDown, FiChevronUp, FiCheckCircle } from 'react-icons/fi'

export default function Query() {
  const [q, setQ] = useState('')
  const [versionId, setVersionId] = useState('')
  const [versions, setVersions] = useState<any[]>([])
  const [selectedVersion, setSelectedVersion] = useState<any>(null)
  const [isVersionDropdownOpen, setIsVersionDropdownOpen] = useState(false)
  const [versionSearchTerm, setVersionSearchTerm] = useState('')
  const [highlightedIndex, setHighlightedIndex] = useState(-1)
  const [answer, setAnswer] = useState<string>('')
  const [sources, setSources] = useState<any[]>([])
  const [versionInfo, setVersionInfo] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [loadingVersions, setLoadingVersions] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const { open: isSourcesOpen, onToggle: toggleSources } = useDisclosure()
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Fetch available versions on component mount
  useEffect(() => {
    const fetchVersions = async () => {
      setLoadingVersions(true)
      try {
        const res = await fetch('/api/versions')
        const json = await res.json()
        if (res.ok) {
          setVersions(json.versions || [])
        }
      } catch (e) {
        console.error('Failed to fetch versions:', e)
      } finally {
        setLoadingVersions(false)
      }
    }
    fetchVersions()
  }, [])

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsVersionDropdownOpen(false)
      }
    }

    if (isVersionDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isVersionDropdownOpen])

  // Filter versions based on search term
  const filteredVersions = versions.filter(version =>
    version.version_name.toLowerCase().includes(versionSearchTerm.toLowerCase()) ||
    version.version_id.toLowerCase().includes(versionSearchTerm.toLowerCase())
  )

  // Show suggestions when typing
  const showSuggestions = versionSearchTerm.length > 0 && filteredVersions.length > 0

  // Select a version
  const selectVersion = (version: any) => {
    setSelectedVersion(version)
    setVersionId(version ? version.version_id : '')
    setIsVersionDropdownOpen(false)
    setVersionSearchTerm('')
  }

  // Handle search input change
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setVersionSearchTerm(value)
    setHighlightedIndex(-1)
    if (value.length > 0) {
      setIsVersionDropdownOpen(true)
    }
  }

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isVersionDropdownOpen && !showSuggestions) return

    const totalOptions = filteredVersions.length + 1 // +1 for "Latest version" option

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setHighlightedIndex(prev => (prev + 1) % totalOptions)
        break
      case 'ArrowUp':
        e.preventDefault()
        setHighlightedIndex(prev => prev <= 0 ? totalOptions - 1 : prev - 1)
        break
      case 'Enter':
        e.preventDefault()
        if (highlightedIndex === 0) {
          selectVersion(null)
        } else if (highlightedIndex > 0) {
          selectVersion(filteredVersions[highlightedIndex - 1])
        }
        break
      case 'Escape':
        setIsVersionDropdownOpen(false)
        setHighlightedIndex(-1)
        break
    }
  }

  // Clear version selection
  const clearVersion = () => {
    setSelectedVersion(null)
    setVersionId('')
    setIsVersionDropdownOpen(false)
    setVersionSearchTerm('')
  }

  // Format date for display
  const formatDate = (timestamp: string) => {
    return new Date(timestamp).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const submit = async () => {
    setLoading(true)
    setError(null)
    setSuccess(null)
    setAnswer('')
    setSources([])
    setVersionInfo(null)
    try {
      const params = new URLSearchParams({ q })
      if (versionId) params.set('version_id', versionId)
      const res = await fetch(`/api/query?${params.toString()}`)
      const json = await res.json()
      if (!res.ok) throw new Error(json.detail || res.statusText)
      setAnswer(json.answer || '')
      setSources(json.sources || [])
      setVersionInfo(json.version_info || null)
      setSuccess('Query successful!')
    } catch (e: any) {
      setError(e.message)
    } finally { setLoading(false) }
  }

  return (
    <VStack gap={8} align="stretch" className="animate-fade-in">
      <Box textAlign="center">
            <Heading size="2xl" color="gray.800" mb={2}>
              Query Documents
            </Heading>
            <Text color="gray.600" fontSize="lg">
              Ask questions about your uploaded documents using AI-powered search
            </Text>
      </Box>

      {/* Query Form Card */}
      <Box className="glass-card" p={8}>
        <VStack gap={6} align="stretch">
          <Box>
                <Heading size="lg" mb={2} color="gray.800">
                  Ask a Question
                </Heading>
                <Text color="gray.600">
                  Get intelligent answers from your document collection
                </Text>
          </Box>

          <VStack gap={4} align="stretch">
            {/* Question Input */}
            <Box>
                  <Text mb={2} color="gray.800" fontWeight="500">Question</Text>
              <Textarea
                placeholder="What functions are available in the codebase?"
                value={q}
                onChange={e => setQ(e.target.value)}
                size="lg"
                variant="outline"
                color="gray.800"
                _placeholder={{ color: 'gray.500' }}
                minH="120px"
                resize="vertical"
                onKeyDown={e => {
                  if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                    e.preventDefault()
                    if (!loading) submit()
                  }
                }}
              />
              <Text fontSize="xs" color="gray.500" mt={1}>
                Press Ctrl+Enter (or Cmd+Enter on Mac) to submit
              </Text>
            </Box>

            {/* Version Selection */}
            <Box>
                  <Text mb={2} color="gray.800" fontWeight="500">Select Version (Optional)</Text>
              
              {/* Selected Version Display */}
              {selectedVersion && (
                <Box mb={2}>
                  <HStack
                    gap={2}
                    p={2}
                    className="glass"
                    borderRadius="20px"
                    w="fit-content"
                  >
                    <Icon as={FiCheckCircle} color="blue.400" boxSize={4} />
                    <Text color="blue.400" fontSize="sm" fontWeight="500">
                      {selectedVersion.version_name}
                    </Text>
                    <Button
                      size="xs"
                      variant="ghost"
                      color="red.400"
                      onClick={clearVersion}
                      _hover={{ background: 'rgba(255, 0, 0, 0.1)' }}
                    >
                      <Icon as={FiX} />
                    </Button>
                  </HStack>
                </Box>
              )}

              {/* Version Dropdown */}
              <Box position="relative" ref={dropdownRef}>
                <Box
                  onClick={() => setIsVersionDropdownOpen(!isVersionDropdownOpen)}
                  className="glass"
                  p={3}
                  borderRadius="12px"
                  cursor={loadingVersions ? 'not-allowed' : 'pointer'}
                  opacity={loadingVersions ? 0.6 : 1}
                  transition="all 0.3s ease"
                  _hover={{ background: 'rgba(255, 255, 255, 0.15)' }}
                >
                  <HStack gap={3}>
                    <Icon as={FiSearch} color="gray.500" />
                    <Input
                      placeholder="Search versions..."
                      value={versionSearchTerm}
                      onChange={handleSearchChange}
                      onKeyDown={handleKeyDown}
                      onClick={e => e.stopPropagation()}
                      disabled={loadingVersions}
                      variant="outline"
                      color="gray.800"
                      _placeholder={{ color: 'gray.500' }}
                    />
                    <Text color="gray.500" fontSize="sm">
                      {selectedVersion ? selectedVersion.version_name : 'Latest version (default)'}
                    </Text>
                  </HStack>
                </Box>

                {(isVersionDropdownOpen || showSuggestions) && !loadingVersions && (
                  <Box
                    position="absolute"
                    top="100%"
                    left={0}
                    right={0}
                    bg="white"
                    border="1px solid"
                    borderColor="gray.200"
                    borderRadius="0 0 12px 12px"
                    maxH="300px"
                    overflowY="auto"
                    zIndex={1000}
                    mt={1}
                    boxShadow="0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)"
                  >
                    {/* Suggestions header */}
                    {showSuggestions && (
                      <Box px={3} py={2} borderBottom="1px solid" borderColor="gray.100">
                        <Text color="gray.600" fontSize="xs" fontWeight="500" textTransform="uppercase" letterSpacing="wide">
                          Suggestions
                        </Text>
                      </Box>
                    )}

                    {/* Latest version option */}
                    <Box
                      onClick={() => {
                        selectVersion(null)
                        setIsVersionDropdownOpen(false)
                      }}
                      p={3}
                      cursor="pointer"
                      borderBottom="1px solid"
                      borderColor="gray.100"
                      bg={highlightedIndex === 0 ? 'blue.100' : (!selectedVersion ? 'blue.50' : 'transparent')}
                      _hover={{ background: 'gray.50' }}
                    >
                      <HStack gap={3}>
                        <Text color={!selectedVersion ? 'blue.500' : 'gray.400'}>
                          {!selectedVersion ? '●' : '○'}
                        </Text>
                        <VStack align="start" gap={1} flex={1}>
                          <Text color="gray.800" fontWeight="500" fontSize="sm">
                            Latest version (default)
                          </Text>
                          <Text color="gray.600" fontSize="xs">
                            Use the most recent version
                          </Text>
                        </VStack>
                      </HStack>
                    </Box>

                    {/* Filtered versions */}
                    {filteredVersions.length === 0 ? (
                      <Box p={3} textAlign="center">
                        <Text color="gray.600" fontSize="sm">
                          No versions found
                        </Text>
                      </Box>
                    ) : (
                      filteredVersions.map((version, index) => (
                        <Box
                          key={version.version_id}
                          onClick={() => {
                            selectVersion(version)
                            setIsVersionDropdownOpen(false)
                          }}
                          p={3}
                          cursor="pointer"
                          borderBottom="1px solid"
                          borderColor="gray.100"
                          bg={highlightedIndex === index + 1 ? 'blue.100' : (selectedVersion?.version_id === version.version_id ? 'blue.50' : 'transparent')}
                          _hover={{ background: 'gray.50' }}
                        >
                          <HStack gap={3}>
                            <Text color={selectedVersion?.version_id === version.version_id ? 'blue.500' : 'gray.400'}>
                              {selectedVersion?.version_id === version.version_id ? '●' : '○'}
                            </Text>
                            <VStack align="start" gap={1} flex={1}>
                              <Text color="gray.800" fontWeight="500" fontSize="sm">
                                {version.version_name}
                              </Text>
                              <Text color="gray.600" fontSize="xs">
                                {version.version_id} • {formatDate(version.upload_timestamp)} • {version.file_count} files
                              </Text>
                            </VStack>
                          </HStack>
                        </Box>
                      ))
                    )}
                  </Box>
                )}
              </Box>

              {loadingVersions && (
                <HStack gap={2} mt={2}>
                  <Spinner size="sm" color="blue.400" />
                  <Text fontSize="sm" color="gray.500">
                    Loading versions...
                  </Text>
                </HStack>
              )}
            </Box>

            <Button
              onClick={submit}
              disabled={!q || loading}
              colorScheme="blue"
              size="lg"
              className="hover-lift"
            >
              <HStack gap={2}>
                {loading ? <Spinner size="sm" /> : <Icon as={FiSearch} />}
                <Text>{loading ? 'Searching...' : 'Ask Question'}</Text>
              </HStack>
            </Button>
          </VStack>
        </VStack>
      </Box>

      {/* Loading State */}
      {loading && (
        <Box className="glass-card" p={6}>
          <VStack gap={4}>
            <HStack gap={3}>
              <Spinner color="blue.400" />
              <Text color="gray.800" fontWeight="500">
                Searching through documents...
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
        <Box className="glass" p={4} borderRadius="12px" bg="green.500" color="gray.800">
          <HStack gap={2}>
            <Icon as={FiCheckCircle} />
            <Text fontWeight="500">{success}</Text>
          </HStack>
        </Box>
      )}

      {/* Error Message */}
      {error && (
        <Box className="glass" p={4} borderRadius="12px" bg="red.500" color="gray.800">
          <VStack gap={2} align="start">
            <Text fontWeight="500">Query Error</Text>
            <Text fontSize="sm">{error}</Text>
          </VStack>
        </Box>
      )}

      {/* Results */}
      {!!answer && (
        <VStack gap={6} align="stretch">
          {/* Version Info - More Prominent */}
          {versionInfo && (
            <Box className="glass-card" p={4} borderRadius="12px">
              <VStack gap={2} align="start">
                <HStack gap={2}>
                  <Icon as={FiCheckCircle} color="blue.400" boxSize={5} />
                  <Heading size="sm" color="gray.800">
                    Analyzing: {versionInfo.version_name}
                  </Heading>
                </HStack>
                {versionInfo.description && (
                  <Text color="gray.600" fontSize="sm" pl={7}>
                    {versionInfo.description}
                  </Text>
                )}
              </VStack>
            </Box>
          )}

          {/* Answer Card */}
          <Box className="glass-card" p={6}>
            <VStack gap={4} align="stretch">
              <HStack gap={3}>
                <Icon as={FiCheckCircle} color="green.400" boxSize={5} />
                <Heading size="md" color="green.400">
                  Answer
                </Heading>
              </HStack>
              <Box
                color="gray.800"
                lineHeight={1.7}
                fontSize="md"
                className="animate-slide-up markdown-content"
              >
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {answer}
                </ReactMarkdown>
              </Box>
            </VStack>
          </Box>

          {/* Sources Card - Hidden by default */}
          {sources.length > 0 && (
            <Box className="glass-card" p={6}>
              <VStack gap={4} align="stretch">
                <HStack justify="space-between">
                  <HStack gap={3}>
                    <Icon as={FiFile} color="blue.400" boxSize={5} />
                    <Heading size="md" color="blue.400">
                      Sources
                    </Heading>
                  </HStack>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={toggleSources}
                    color="gray.600"
                  >
                    <HStack gap={1}>
                      {isSourcesOpen ? <FiChevronUp /> : <FiChevronDown />}
                      <Text>{isSourcesOpen ? 'Hide' : 'Show'} ({sources.length})</Text>
                    </HStack>
                  </Button>
                </HStack>

                <Box display={isSourcesOpen ? 'block' : 'none'}>
                  <VStack gap={3} align="stretch">
                    <Text fontSize="sm" color="gray.600">
                      Found {sources.length} source{sources.length !== 1 ? 's' : ''}
                    </Text>
                    {sources.map((s, i) => (
                      <Box
                        key={i}
                        className="glass hover-lift"
                        p={3}
                        borderRadius="8px"
                      >
                        <VStack gap={2} align="stretch">
                          <HStack gap={2}>
                            <Icon as={FiFile} color="gray.500" boxSize={4} />
                            <Text
                              color="gray.800"
                              fontWeight="500"
                              fontSize="sm"
                              overflow="hidden"
                              textOverflow="ellipsis"
                              whiteSpace="nowrap"
                            >
                              {s.file.split('/').pop()}
                            </Text>
                          </HStack>
                          <HStack gap={2} wrap="wrap">
                            <Badge colorScheme="blue" size="sm">
                              {s.file_extension}
                            </Badge>
                            {s.chunk_name && (
                              <Badge colorScheme="green" size="sm">
                                {s.chunk_name}
                              </Badge>
                            )}
                          </HStack>
                          <Text
                            color="gray.600"
                            fontSize="xs"
                            overflow="hidden"
                            textOverflow="ellipsis"
                            display="-webkit-box"
                            style={{
                              WebkitLineClamp: 2,
                              WebkitBoxOrient: 'vertical'
                            }}
                          >
                            {s.content_preview}
                          </Text>
                        </VStack>
                      </Box>
                    ))}
                  </VStack>
                </Box>
              </VStack>
            </Box>
          )}
        </VStack>
      )}
    </VStack>
  )
}


