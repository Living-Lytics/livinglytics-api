import './App.css'
import Pages from "@/pages/index.jsx"
import { Toaster } from "@/components/ui/toaster"
import SignInModal from "@/components/auth/SignInModal"

function App() {
  return (
    <>
      <Pages />
      <Toaster />
      <SignInModal />
    </>
  )
}

export default App 