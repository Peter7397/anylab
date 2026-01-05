/**
 * File Hash Utility
 * 
 * Calculates SHA-256 hash of files using Web Crypto API.
 * Supports chunked reading for large files and progress reporting.
 */

/**
 * Calculate SHA-256 hash of a file
 * 
 * @param file - File object to hash
 * @param onProgress - Optional callback for progress updates (0-100)
 * @returns Promise resolving to lowercase hex hash string (64 characters)
 * @throws Error if hash calculation fails
 */
export async function calculateFileHash(
  file: File,
  onProgress?: (progress: number) => void
): Promise<string> {
  // Check if Web Crypto API is available
  if (!window.crypto || !window.crypto.subtle) {
    throw new Error('Web Crypto API is not available in this browser');
  }

  try {
    // Read file in chunks to avoid blocking UI
    const chunkSize = 1024 * 1024; // 1MB chunks
    const fileSize = file.size;
    let bytesRead = 0;
    let lastProgress = 0;

    // Create a hash context
    const hashBuffer = await crypto.subtle.digest(
      'SHA-256',
      await readFileInChunks(file, chunkSize, (chunkBytesRead) => {
        bytesRead += chunkBytesRead;
        
        // Calculate progress percentage
        const progress = fileSize > 0 ? Math.floor((bytesRead / fileSize) * 100) : 100;
        
        // Only fire callback if progress changed significantly (avoid spam)
        if (progress !== lastProgress && onProgress) {
          onProgress(Math.min(progress, 100));
          lastProgress = progress;
        }
      })
    );

    // Convert ArrayBuffer to hex string
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    
    // Final progress callback
    if (onProgress) {
      onProgress(100);
    }

    return hashHex.toLowerCase();
  } catch (error) {
    throw new Error(`Failed to calculate file hash: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Read file in chunks and return as ArrayBuffer
 * 
 * @param file - File to read
 * @param chunkSize - Size of each chunk in bytes
 * @param onChunkRead - Callback when a chunk is read
 * @returns Promise resolving to ArrayBuffer containing file content
 */
async function readFileInChunks(
  file: File,
  chunkSize: number,
  onChunkRead?: (bytesRead: number) => void
): Promise<ArrayBuffer> {
  const chunks: Uint8Array[] = [];
  let offset = 0;

  while (offset < file.size) {
    const chunk = file.slice(offset, offset + chunkSize);
    const arrayBuffer = await chunk.arrayBuffer();
    const uint8Array = new Uint8Array(arrayBuffer);
    
    chunks.push(uint8Array);
    offset += chunkSize;
    
    if (onChunkRead) {
      onChunkRead(uint8Array.length);
    }
  }

  // Combine all chunks into single ArrayBuffer
  const totalLength = chunks.reduce((sum, chunk) => sum + chunk.length, 0);
  const result = new Uint8Array(totalLength);
  let position = 0;

  for (const chunk of chunks) {
    result.set(chunk, position);
    position += chunk.length;
  }

  return result.buffer;
}

/**
 * Calculate hash for multiple files with progress tracking and cancellation support
 * 
 * @param files - Array of files to hash
 * @param onFileProgress - Callback for individual file progress (fileIndex, progress)
 * @param onOverallProgress - Callback for overall progress (completed, total)
 * @param shouldCancel - Function that returns true if calculation should be cancelled
 * @returns Promise resolving to array of {file, hash} objects
 */
export async function calculateFileHashes(
  files: File[],
  onFileProgress?: (fileIndex: number, progress: number) => void,
  onOverallProgress?: (completed: number, total: number) => void,
  shouldCancel?: () => boolean
): Promise<Array<{ file: File; hash: string }>> {
  const results: Array<{ file: File; hash: string }> = [];
  let completed = 0;

  for (let i = 0; i < files.length; i++) {
    // Check for cancellation
    if (shouldCancel && shouldCancel()) {
      throw new Error('Hash calculation cancelled by user');
    }

    const file = files[i];
    
    try {
      const hash = await calculateFileHash(file, (progress) => {
        // Check for cancellation during hash calculation
        if (shouldCancel && shouldCancel()) {
          throw new Error('Hash calculation cancelled by user');
        }
        
        if (onFileProgress) {
          onFileProgress(i, progress);
        }
      });

      results.push({ file, hash });
      completed++;

      if (onOverallProgress) {
        onOverallProgress(completed, files.length);
      }
    } catch (error) {
      // If cancelled, re-throw cancellation error
      if (error instanceof Error && error.message.includes('cancelled')) {
        throw error;
      }
      // Otherwise, throw error for this file
      throw new Error(`Failed to hash file "${file.name}": ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  return results;
}

/**
 * Validate hash format (SHA-256 hex string)
 * 
 * @param hash - Hash string to validate
 * @returns true if hash is valid, false otherwise
 */
export function isValidHash(hash: string): boolean {
  // SHA-256 produces 64 character hex string
  return /^[0-9a-f]{64}$/i.test(hash);
}

