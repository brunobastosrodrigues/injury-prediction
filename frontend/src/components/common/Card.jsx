function Card({ title, children, className = '', actions }) {
  return (
    <div className={`bg-white dark:bg-slate-900/50 rounded-2xl border border-gray-200 dark:border-slate-800 shadow-sm dark:shadow-none ${className}`}>
      {title && (
        <div className="px-6 py-4 border-b border-gray-200 dark:border-slate-800 flex justify-between items-center">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{title}</h3>
          {actions && <div className="flex space-x-2">{actions}</div>}
        </div>
      )}
      <div className="p-6">{children}</div>
    </div>
  )
}

export default Card
