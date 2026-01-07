export default function Navbar() {
  return (
    <nav className="bg-gray-900 text-white p-4">
      <div className="max-w-6xl mx-auto flex items-center justify-between">
        <div className="font-semibold">JD Admin</div>
        <div className="space-x-4">
          <a href="#" className="text-sm opacity-90">Create</a>
          <a href="#" className="text-sm opacity-90">List</a>
        </div>
      </div>
    </nav>
  );
}
