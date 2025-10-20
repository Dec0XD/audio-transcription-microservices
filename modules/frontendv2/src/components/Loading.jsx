export default function Loading({ message = 'Carregando...' }) {
  return (
    <div className="flex items-center justify-center min-h-[200px]">
      <div className="text-center">
        <div className="relative w-16 h-16 mx-auto mb-4">
          <div className="absolute top-0 left-0 w-full h-full">
            <div className="w-16 h-16 rounded-full border-4 border-gray-200"></div>
          </div>
          <div className="absolute top-0 left-0 w-full h-full animate-spin">
            <div className="w-16 h-16 rounded-full border-4 border-primary-600 border-t-transparent"></div>
          </div>
        </div>
        <p className="text-gray-600 font-medium">{message}</p>
      </div>
    </div>
  )
}

export function LoadingSpinner({ size = 'md', className = '' }) {
  const sizes = {
    sm: 'w-4 h-4 border-2',
    md: 'w-8 h-8 border-3',
    lg: 'w-12 h-12 border-4',
  }

  return (
    <div className={`inline-block ${className}`}>
      <div className={`${sizes[size]} rounded-full border-primary-600 border-t-transparent animate-spin`}></div>
    </div>
  )
}

export function LoadingSkeleton({ lines = 3, className = '' }) {
  return (
    <div className={`space-y-3 ${className}`}>
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} className="animate-shimmer h-4 bg-gray-200 rounded"></div>
      ))}
    </div>
  )
}
