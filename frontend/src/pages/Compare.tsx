import { useState, useEffect, useRef } from 'react'
import {
  Box,
  VStack,
  HStack,
  Heading,
  Text,
  Button,
  Input,
  Textarea,
  Icon,
  Spinner,
  Badge,
  Code,
  Flex,
  Grid,
  useDisclosure
} from '@chakra-ui/react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { FiSearch, FiX, FiCopy, FiCalendar, FiFile, FiRefreshCw, FiCheckCircle, FiAlertCircle } from 'react-icons/fi'

export default function Compare() {
  const [versions, setVersions] = useState<any[]>([])
  const [selectedVersions, setSelectedVersions] = useState<string[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const [q, setQ] = useState('')
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [versionsLoading, setVersionsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const [highlightedIndex, setHighlightedIndex] = useState(-1)

  const loadVersions = async () => {
    setVersionsLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/versions')
      const json = await res.json()
      if (!res.ok) throw new Error(json.detail || res.statusText)
      setVersions(json.versions || [])
      setSuccess('Versions loaded successfully')
    } catch (e: any) {
      setError(`Failed to load versions: ${e.message}`)
    } finally {
      setVersionsLoading(false)
    }
  }

  useEffect(() => {
    loadVersions()
  }, [])

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false)
      }
    }

    if (isDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isDropdownOpen])

  const filteredVersions = versions.filter(version =>
    version.version_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    version.version_id.toLowerCase().includes(searchTerm.toLowerCase())
  )

  // Show suggestions when typing
  const showSuggestions = searchTerm.length > 0 && filteredVersions.length > 0

  const toggleVersionSelection = (versionId: string) => {
    setSelectedVersions(prev => 
      prev.includes(versionId) 
        ? prev.filter(id => id !== versionId)
        : [...prev, versionId]
    )
  }

  const removeVersion = (versionId: string) => {
    setSelectedVersions(prev => prev.filter(id => id !== versionId))
  }

  const clearSelection = () => {
    setSelectedVersions([])
  }

  // Handle search input change
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setSearchTerm(value)
    setHighlightedIndex(-1)
    if (value.length > 0) {
      setIsDropdownOpen(true)
    }
  }

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isDropdownOpen && !showSuggestions) return

    const totalOptions = filteredVersions.length

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
        if (highlightedIndex >= 0 && highlightedIndex < filteredVersions.length) {
          toggleVersionSelection(filteredVersions[highlightedIndex].version_id)
        }
        break
      case 'Escape':
        setIsDropdownOpen(false)
        setHighlightedIndex(-1)
        break
    }
  }

  const formatDate = (timestamp: string) => {
    return new Date(timestamp).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setSuccess('Answer copied to clipboard!')
    setTimeout(() => setSuccess(null), 2000)
  }

  const submit = async () => {
    if (selectedVersions.length < 2) {
      setError('Please select at least 2 versions to compare')
      return
    }
    
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const params = new URLSearchParams({ 
        q, 
        version_ids: selectedVersions.join(',') 
      })
      const res = await fetch(`/api/query_compare?${params.toString()}`)
      const json = await res.json()
      if (!res.ok) throw new Error(json.detail || res.statusText)
      setResult(json)
      setSuccess('Comparison completed successfully!')
    } catch (e: any) {
      setError(`Comparison failed: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <VStack gap={8} align="stretch" className="animate-fade-in">
      <Box textAlign="center">
        <Heading size="2xl" color="gray.800" mb={2}>
          Compare Versions
        </Heading>
        <Text color="gray.600" fontSize="lg">
          Compare answers across different document versions
        </Text>
      </Box>

      {/* Header with Refresh Button */}
      <Flex justify="space-between" align="center">
        <Box />
        <Button
          onClick={loadVersions}
          disabled={versionsLoading}
          colorScheme="blue"
          variant="outline"
          className="hover-lift"
        >
          <HStack gap={2}>
            {versionsLoading ? <Spinner size="sm" /> : <Icon as={FiRefreshCw} />}
            <Text>{versionsLoading ? 'Loading...' : 'Refresh Versions'}</Text>
          </HStack>
        </Button>
      </Flex>

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

      {/* Question Input */}
      <Box className="glass-card" p={6}>
        <VStack gap={4} align="stretch">
          <Heading size="md" color="gray.800">
            Question
          </Heading>
          <Textarea
            placeholder="Enter your question to compare across versions..."
            value={q}
            onChange={e => setQ(e.target.value)}
            minH="100px"
            variant="outline"
            color="gray.800"
            _placeholder={{ color: 'gray.500' }}
          />
        </VStack>
      </Box>

      {/* Version Selection */}
      <Box className="glass-card" p={6}>
        <VStack gap={4} align="stretch">
          <Heading size="md" color="gray.800">
            Select Versions to Compare (minimum 2)
          </Heading>

          {/* Search Dropdown */}
          <Box position="relative" ref={dropdownRef}>
            <Box
              onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              className="glass"
              p={3}
              borderRadius="12px"
              cursor="pointer"
              transition="all 0.3s ease"
              _hover={{ background: 'rgba(255, 255, 255, 0.15)' }}
            >
              <HStack gap={3}>
                <Icon as={FiSearch} color="gray.500" />
                <Input
                  placeholder="Search versions..."
                  value={searchTerm}
                  onChange={handleSearchChange}
                  onKeyDown={handleKeyDown}
                  onClick={e => e.stopPropagation()}
                  variant="outline"
                  color="gray.800"
                  _placeholder={{ color: 'gray.500' }}
                />
                <Text color="gray.500" fontSize="sm">
                  {selectedVersions.length} selected
                </Text>
              </HStack>
            </Box>

            {(isDropdownOpen || showSuggestions) && (
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
                        toggleVersionSelection(version.version_id)
                        // Don't close dropdown for multi-select
                      }}
                      p={3}
                      cursor="pointer"
                      borderBottom="1px solid"
                      borderColor="gray.100"
                      bg={highlightedIndex === index ? 'blue.100' : (selectedVersions.includes(version.version_id) ? 'blue.50' : 'transparent')}
                      _hover={{ background: 'gray.50' }}
                    >
                      <HStack gap={3}>
                        <Text color={selectedVersions.includes(version.version_id) ? 'blue.500' : 'gray.400'}>
                          {selectedVersions.includes(version.version_id) ? '●' : '○'}
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

          {/* Selected Versions */}
          {selectedVersions.length > 0 && (
            <Box>
              <HStack gap={2} mb={3}>
                <Text color="gray.800" fontWeight="500" fontSize="sm">
                  Selected Versions:
                </Text>
                <Button
                  onClick={clearSelection}
                  size="xs"
                  variant="outline"
                  color="gray.500"
                >
                  Clear All
                </Button>
              </HStack>
              <HStack gap={2} wrap="wrap">
                {selectedVersions.map(versionId => {
                  const version = versions.find(v => v.version_id === versionId)
                  return (
                    <HStack
                      key={versionId}
                      gap={2}
                      className="glass"
                      px={3}
                      py={2}
                      borderRadius="20px"
                    >
                      <Text color="blue.600" fontSize="sm" fontWeight="500">
                        {version?.version_name || versionId}
                      </Text>
                      <Button
                        onClick={() => removeVersion(versionId)}
                        size="xs"
                        variant="ghost"
                        color="blue.600"
                        p={0}
                        minW="auto"
                        h="auto"
                      >
                        <Icon as={FiX} boxSize={3} />
                      </Button>
                    </HStack>
                  )
                })}
              </HStack>
            </Box>
          )}

          {/* Compare Button */}
          <Button
            onClick={submit}
            disabled={!q.trim() || selectedVersions.length < 2 || loading}
            colorScheme="blue"
            size="lg"
            className="hover-lift"
          >
            <HStack gap={2}>
              {loading ? <Spinner size="sm" /> : <Icon as={FiSearch} />}
              <Text>{loading ? 'Comparing...' : 'Compare Versions'}</Text>
            </HStack>
          </Button>
        </VStack>
      </Box>

      {/* Results */}
      {result && (
        <Box className="glass-card" p={6}>
          <VStack gap={6} align="stretch">
            <HStack gap={3}>
              <Icon as={FiCheckCircle} color="green.400" boxSize={5} />
              <Heading size="md" color="green.600">
                Comparison Results
              </Heading>
            </HStack>

            <Grid templateColumns={{ base: '1fr', md: 'repeat(2, 1fr)', lg: 'repeat(3, 1fr)' }} gap={4}>
              {result.comparison_results.map((item: any, index: number) => (
                <Box
                  key={item.version_id}
                  className="glass hover-lift"
                  p={4}
                  borderRadius="12px"
                >
                  <VStack gap={3} align="stretch">
                    {/* Header */}
                    <Flex justify="space-between" align="flex-start">
                      <VStack align="start" gap={1}>
                        <HStack gap={2}>
                          <Text fontSize="lg">📦</Text>
                          <Heading size="sm" color="gray.800">
                            Version: {item.version_name}
                          </Heading>
                        </HStack>
                        <Text fontSize="xs" color="gray.600" fontFamily="monospace">
                          {item.version_id}
                        </Text>
                        {item.description && (
                          <Text fontSize="xs" color="gray.600" fontStyle="italic">
                            {item.description}
                          </Text>
                        )}
                      </VStack>
                      <Button
                        onClick={() => copyToClipboard(item.answer)}
                        size="sm"
                        variant="ghost"
                        color="gray.500"
                        p={1}
                        minW="auto"
                        h="auto"
                        title="Copy answer"
                      >
                        <Icon as={FiCopy} boxSize={4} />
                      </Button>
                    </Flex>

                    {/* Answer */}
                    <Box>
                      <Text color="gray.800" fontWeight="500" fontSize="sm" mb={2}>
                        Answer:
                      </Text>
                      <Box
                        color="gray.700"
                        fontSize="sm"
                        lineHeight={1.6}
                        className="markdown-content-small"
                      >
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {item.answer}
                        </ReactMarkdown>
                      </Box>
                    </Box>

                    {/* Footer */}
                    <HStack justify="space-between" align="center" pt={2} borderTop="1px solid rgba(255, 255, 255, 0.2)">
                      <HStack gap={2} color="gray.500" fontSize="xs">
                        <Icon as={FiFile} boxSize={3} />
                        <Text>{item.sources_count} sources</Text>
                      </HStack>
                      {item.error && (
                        <Text color="red.500" fontWeight="500" fontSize="xs">
                          Error: {item.error}
                        </Text>
                      )}
                    </HStack>
                  </VStack>
                </Box>
              ))}
            </Grid>
          </VStack>
        </Box>
      )}
    </VStack>
  )
}