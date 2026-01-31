import { Sidebar } from './components/Sidebar'
import { Chat } from './components/Chat'

function App() {
  return (
    <div className="flex bg-[#171717] h-screen w-screen text-slate-200 overflow-hidden">
      <Sidebar />
      <main className="flex-1 flex flex-col relative overflow-hidden bg-[#171717]">
        <Chat />
      </main>
    </div>
  )
}

export default App
