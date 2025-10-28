import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, X, FileImage } from 'lucide-react';

const NewEvaluationPage = () => {
  const [examId, setExamId] = useState('CS-101');
  const [targetQuestion, setTargetQuestion] = useState('Question 1');
  const [rubricText, setRubricText] = useState('');
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();

  const handleFileChange = (file) => {
    if (file && file.type.startsWith('image/')) {
      setImageFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    handleFileChange(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const removeImage = () => {
    setImageFile(null);
    setImagePreview(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!imageFile) {
      alert('Please select an image file');
      return;
    }

    setIsSubmitting(true);

    try {
      const reader = new FileReader();
      reader.onloadend = async () => {
        const base64String = reader.result.split(',')[1];

        const payload = {
          exam_id: examId,
          rubric_text: rubricText,
          image_b64: base64String,
          target_question: targetQuestion,
        };

        const response = await fetch('http://localhost:8000/v1/evaluate', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          throw new Error('Failed to submit evaluation');
        }

        const data = await response.json();
        navigate(`/results/${data.task_id}`);
      };

      reader.readAsDataURL(imageFile);
    } catch (error) {
      console.error('Error submitting evaluation:', error);
      alert('Failed to submit evaluation. Please try again.');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-4xl font-bold text-white mb-8">Submit New Answer for Grading</h1>

      <form onSubmit={handleSubmit} className="glass-card p-8 space-y-6">
        <div className="grid grid-cols-2 gap-6">
          <div>
            <label htmlFor="examId" className="block text-sm font-medium text-gray-300 mb-2">
              Exam ID
            </label>
            <input
              type="text"
              id="examId"
              value={examId}
              onChange={(e) => setExamId(e.target.value)}
              className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
              required
            />
          </div>

          <div>
            <label htmlFor="targetQuestion" className="block text-sm font-medium text-gray-300 mb-2">
              Target Question
            </label>
            <input
              type="text"
              id="targetQuestion"
              value={targetQuestion}
              onChange={(e) => setTargetQuestion(e.target.value)}
              className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
              required
            />
          </div>
        </div>

        <div>
          <label htmlFor="rubric" className="block text-sm font-medium text-gray-300 mb-2">
            Grading Rubric
          </label>
          <textarea
            id="rubric"
            value={rubricText}
            onChange={(e) => setRubricText(e.target.value)}
            rows={6}
            className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all resize-none"
            placeholder="Enter the grading rubric here..."
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Answer Sheet Image
          </label>

          {!imagePreview ? (
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-all ${
                isDragging
                  ? 'border-purple-500 bg-purple-500/10'
                  : 'border-white/20 bg-white/5 hover:border-white/40'
              }`}
            >
              <input
                type="file"
                accept="image/*"
                onChange={(e) => handleFileChange(e.target.files[0])}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-300 mb-2">
                Drag and drop your image here, or click to browse
              </p>
              <p className="text-sm text-gray-500">Supports: JPG, PNG, GIF</p>
            </div>
          ) : (
            <div className="relative border border-white/20 rounded-lg p-4 bg-white/5">
              <button
                type="button"
                onClick={removeImage}
                className="absolute top-6 right-6 p-2 bg-red-500/80 hover:bg-red-600 rounded-full transition-all"
              >
                <X className="w-4 h-4 text-white" />
              </button>
              <div className="flex items-start space-x-4">
                <img
                  src={imagePreview}
                  alt="Preview"
                  className="w-32 h-32 object-cover rounded-lg border border-white/20"
                />
                <div className="flex-1">
                  <div className="flex items-center space-x-2 text-gray-300 mb-2">
                    <FileImage className="w-5 h-5" />
                    <span className="font-medium">{imageFile.name}</span>
                  </div>
                  <p className="text-sm text-gray-500">
                    {(imageFile.size / 1024).toFixed(2)} KB
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full py-4 px-6 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed text-white font-semibold text-lg rounded-lg transition-all duration-200 shadow-lg hover:shadow-purple-500/50"
        >
          {isSubmitting ? 'Submitting...' : 'Begin Evaluation'}
        </button>
      </form>
    </div>
  );
};

export default NewEvaluationPage;
