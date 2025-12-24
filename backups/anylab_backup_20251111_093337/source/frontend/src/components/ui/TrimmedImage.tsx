import React, { useEffect, useRef, useState } from 'react';

interface TrimmedImageProps {
  src: string;
  alt?: string;
  className?: string;
  fallbackSrc?: string;
}

const TrimmedImage: React.FC<TrimmedImageProps> = ({ src, alt = '', className, fallbackSrc }) => {
  const [renderSrc, setRenderSrc] = useState<string>(src);
  const attemptedFallback = useRef<boolean>(false);
  const processingRef = useRef<boolean>(false);
  const lastProcessedSrc = useRef<string>('');

  useEffect(() => {
    // Reset state when src changes
    if (lastProcessedSrc.current !== src) {
      attemptedFallback.current = false;
      processingRef.current = false;
      lastProcessedSrc.current = src;
      setRenderSrc(src);
    }
    
    // Prevent processing if already processing the same src
    if (processingRef.current) {
      return;
    }

    let active = true;
    processingRef.current = true;
    const currentSrc = lastProcessedSrc.current;
    
    const image = new Image();
    image.crossOrigin = 'anonymous';
    
    image.onload = () => {
      if (!active || currentSrc !== lastProcessedSrc.current) {
        processingRef.current = false;
        return;
      }
      
      try {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        if (!ctx) {
          processingRef.current = false;
          return;
        }
        const w = image.width;
        const h = image.height;
        canvas.width = w;
        canvas.height = h;
        ctx.drawImage(image, 0, 0);
        const imgData = ctx.getImageData(0, 0, w, h).data;

        let top = 0, left = 0, right = w - 1, bottom = h - 1;
        const isRowTransparent = (y: number) => {
          for (let x = 0; x < w; x++) {
            const idx = (y * w + x) * 4 + 3; // alpha
            if (imgData[idx] !== 0) return false;
          }
          return true;
        };
        const isColTransparent = (x: number) => {
          for (let y = 0; y < h; y++) {
            const idx = (y * w + x) * 4 + 3; // alpha
            if (imgData[idx] !== 0) return false;
          }
          return true;
        };

        while (top < bottom && isRowTransparent(top)) top++;
        while (bottom > top && isRowTransparent(bottom)) bottom--;
        while (left < right && isColTransparent(left)) left++;
        while (right > left && isColTransparent(right)) right--;

        const cropW = Math.max(1, right - left + 1);
        const cropH = Math.max(1, bottom - top + 1);

        // draw cropped
        const out = document.createElement('canvas');
        out.width = cropW;
        out.height = cropH;
        const octx = out.getContext('2d');
        if (!octx) {
          processingRef.current = false;
          return;
        }
        octx.drawImage(image, left, top, cropW, cropH, 0, 0, cropW, cropH);
        const dataUrl = out.toDataURL();
        
        // Only update if still active and src hasn't changed
        if (active && currentSrc === lastProcessedSrc.current) {
          setRenderSrc((prev) => prev !== dataUrl ? dataUrl : prev);
        }
        processingRef.current = false;
      } catch {
        processingRef.current = false;
      }
    };
    
    image.onerror = () => {
      if (!active || currentSrc !== lastProcessedSrc.current) {
        processingRef.current = false;
        return;
      }
      
      if (!attemptedFallback.current && fallbackSrc) {
        attemptedFallback.current = true;
        // try fallback
        setRenderSrc((prev) => prev !== fallbackSrc ? fallbackSrc : prev);
        processingRef.current = false;
        return;
      }
      processingRef.current = false;
    };
    
    image.src = currentSrc;
    return () => { 
      active = false;
      processingRef.current = false;
    };
  }, [src, fallbackSrc]);

  return (
    <img src={renderSrc} alt={alt} className={className} />
  );
};

export default TrimmedImage;






