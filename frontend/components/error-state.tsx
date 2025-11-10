import { AlertOctagonIcon } from "lucide-react"

interface Props {
    title: string
    description: string
}

const ErrorState = ({ title, description }: Props) => {
    return (
        <div className="flex items-center justify-center min-h-screen">
            <div className="flex flex-col items-center justify-center bg-background border-2 px-10 py-8 rounded-lg shadow-sm w-fit gap-4">
                <AlertOctagonIcon className="size-8 text-destructive" />
                <div className="flex flex-col text-center gap-2">
                    <h6 className="text-lg font-bold">{title}</h6>
                    <p className="text-sm">{description}</p>
                </div>
            </div>
        </div>
    )
}
export default ErrorState