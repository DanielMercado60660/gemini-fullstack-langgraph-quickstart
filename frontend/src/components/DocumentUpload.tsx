import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";

interface DocumentUploadProps {
  onUpload: (data: unknown) => void;
}

export const DocumentUpload: React.FC<DocumentUploadProps> = ({ onUpload }) => {
  const [progress, setProgress] = useState(0);
  const [uploading, setUploading] = useState(false);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      acceptedFiles.forEach((file) => {
        const formData = new FormData();
        formData.append("file", file);

        const xhr = new XMLHttpRequest();
        xhr.open("POST", "/api/documents/upload");

        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) {
            setUploading(true);
            setProgress((event.loaded / event.total) * 100);
          }
        };

        xhr.onload = () => {
          setUploading(false);
          setProgress(0);
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              const json = JSON.parse(xhr.responseText);
              onUpload(json);
            } catch (err) {
              console.error("Failed to parse server response", err);
            }
          }
        };

        xhr.onerror = () => {
          setUploading(false);
          setProgress(0);
          console.error("Upload failed");
        };

        xhr.send(formData);
      });
    },
    [onUpload]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
  });

  return (
    <div
      {...getRootProps()}
      className="border-2 border-dashed border-neutral-600 rounded-lg p-4 text-neutral-300 text-center cursor-pointer"
    >
      <input {...getInputProps()} />
      {isDragActive ? (
        <p>Drop the PDF here ...</p>
      ) : (
        <p>Drag 'n' drop a PDF here, or click to select one</p>
      )}
      {uploading && (
        <progress
          value={progress}
          max="100"
          className="w-full mt-2 h-2"
        />
      )}
    </div>
  );
};

export default DocumentUpload;
