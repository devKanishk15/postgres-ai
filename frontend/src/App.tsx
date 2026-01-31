import { Sidebar } from './components/Sidebar'
import { Chat } from './components/Chat'

function App() {
  return (
    <div className="flex bg-[#020617] h-screen w-screen text-slate-200 overflow-hidden">
      <Sidebar />
      <main className="flex-1 flex flex-col relative overflow-hidden">
        {/* Background gradient effects */}
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-blue-600/10 blur-[120px] -z-10 rounded-full translate-x-1/2 -translate-y-1/2"></div>
        <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-indigo-600/10 blur-[120px] -z-10 rounded-full -translate-x-1/2 translate-y-1/2"></div>

        <Chat />
      </main>
    </div>
  )
}

export default App
