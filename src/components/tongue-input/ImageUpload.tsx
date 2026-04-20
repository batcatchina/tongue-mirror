import React, { useState, useCallback } from 'react';
import clsx from 'clsx';

interface ImageUploadProps {
  value?: string;
  onChange: (imageData: string | null) => void;
}

export const ImageUpload: React.FC<ImageUploadProps> = ({ value, onChange }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [preview, setPreview] = useState<string | null>(value || null);

  const handleFileSelect = useCallback((file: File) => {
    if (!file.type.startsWith('image/')) {
      alert('请选择图片文件');
      return;
    }
    
    if (file.size > 10 * 1024 * 1024) {
      alert('图片大小不能超过10MB');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const result = e.target?.result as string;
      setPreview(result);
      onChange(result);
    };
    reader.readAsDataURL(file);
  }, [onChange]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFileSelect(file);
  }, [handleFileSelect]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFileSelect(file);
  }, [handleFileSelect]);

  const handleRemove = useCallback(() => {
    setPreview(null);
    onChange(null);
  }, [onChange]);

  return (
    <div className="space-y-3">
      <label className="block text-sm font-medium text-stone-700">
        📷 舌象图片上传
      </label>
      
      {preview ? (
        <div className="relative rounded-xl overflow-hidden border-2 border-primary-200 bg-gradient-to-br from-primary-50 to-secondary-50">
          <img 
            src={preview} 
            alt="舌象预览" 
            className="w-full h-48 object-cover"
          />
          <div className="absolute inset-0 bg-black/40 opacity-0 hover:opacity-100 transition-opacity flex items-center justify-center gap-3">
            <label className="cursor-pointer px-4 py-2 bg-white rounded-lg text-sm font-medium text-stone-700 hover:bg-stone-100 transition-colors">
              重新上传
              <input 
                type="file" 
                accept="image/*" 
                onChange={handleInputChange}
                className="hidden"
              />
            </label>
            <button
              onClick={handleRemove}
              className="px-4 py-2 bg-red-500 text-white rounded-lg text-sm font-medium hover:bg-red-600 transition-colors"
            >
              删除
            </button>
          </div>
          <div className="absolute top-2 right-2 px-2 py-1 bg-green-500 text-white text-xs rounded-full">
            ✓ 已上传
          </div>
          {/* 提示用户确认 */}
          <div className="p-2 bg-amber-50 border-t border-amber-200 text-xs text-amber-700 text-center">
            ⚠️ 请确保上传的是清晰的舌象照片，并手动选择舌象特征
          </div>
        </div>
      ) : (
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          className={clsx(
            'border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 cursor-pointer',
            isDragging
              ? 'border-primary-400 bg-primary-50'
              : 'border-stone-300 bg-stone-50 hover:border-primary-300 hover:bg-primary-50'
          )}
        >
          <input
            type="file"
            accept="image/*"
            onChange={handleInputChange}
            className="hidden"
            id="tongue-image-upload"
          />
          <label htmlFor="tongue-image-upload" className="cursor-pointer">
            <div className="text-4xl mb-3">📷</div>
            <p className="text-stone-600 font-medium">点击或拖拽上传舌象图片</p>
            <p className="text-stone-400 text-sm mt-1">支持 JPG、PNG 格式，最大 10MB</p>
          </label>
        </div>
      )}
    </div>
  );
};

export default ImageUpload;
