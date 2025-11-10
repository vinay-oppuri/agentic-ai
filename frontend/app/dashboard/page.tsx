import { auth } from "@/lib/auth"
import DashboardView from "@/modules/dashboard/ui/views/dashboard-view"
import { headers } from "next/headers"
import { redirect } from "next/navigation"

const Page = async () => {
  const session = await auth.api.getSession({
    headers: await headers()
  })

  if(!session) {
    redirect('/login')
  }

  return <DashboardView/>
}
export default Page