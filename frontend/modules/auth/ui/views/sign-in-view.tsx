"use client"

import { z } from "zod"
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from "react-hook-form"
import { OctagonAlertIcon } from "lucide-react"
import { FaGoogle, FaGithub } from 'react-icons/fa'
import Link from "next/link"

import { useState } from "react"
import { signIn } from "@/lib/auth-client"

import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Alert, AlertTitle } from "@/components/ui/alert"
import { signInFormSchema } from "@/db/schema"



export const SignInView = () => {
    const [error, setError] = useState<string | null>(null)
    const [pending, setPending] = useState(false)

    const form = useForm<z.infer<typeof signInFormSchema>>({
        resolver: zodResolver(signInFormSchema),
        defaultValues: {
            email: "",
            password: ""
        }
    })

    const onSubmit = (data: z.infer<typeof signInFormSchema>) => {
        setError(null)
        setPending(true)

        signIn.email({
            email: data.email,
            password: data.password,
            callbackURL: '/dashboard'
        }, {
            onSuccess: () => {
                setPending(false)
            },
            onError: ({ error }) => {
                setError(error.message)
                setPending(false)
            }
        })
    }

    // const onSocial = (provider: 'github' | 'google') => {
    //     setError(null)
    //     setPending(true)

    //     signIn.social({
    //         provider: provider,
    //         callbackURL: '/dashboard'
    //     }, {
    //         onSuccess: () => {
    //             setPending(false)
    //         },
    //         onError: ({ error }) => {
    //             setError(error.message)
    //             setPending(false)
    //         }
    //     })
    // }

    return (
        <div className="flex flex-col items-center  gap-6">
            <Card className="min-w-md overflow-hidden justify-center border-3 border-gray-900 bg-linear-to-br from-gray-900 to-black p-0">
                <CardContent className="grid grid-cols-1 p-0">
                    <Form {...form}>
                        <form onSubmit={form.handleSubmit(onSubmit)} className="p-6 md:p-8 space-y-6">
                            <div className="text-center space-y-1">
                                <h1 className="flex flex-col py-2 gap-4 text-3xl font-bold tracking-tighter bg-clip-text text-transparent bg-linear-to-r from-purple-400 to-pink-600">
                                    Welcome Back
                                </h1>
                                <p className="text-muted-foreground">Login to your account</p>
                            </div>

                            <FormField
                                control={form.control}
                                name="email"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Email</FormLabel>
                                        <FormControl>
                                            <Input type="email" placeholder="elon@example.com" {...field} />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            <FormField
                                control={form.control}
                                name="password"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Password</FormLabel>
                                        <FormControl>
                                            <Input type="password" placeholder="********" {...field} />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            {!!error && (
                                <Alert className="bg-destructive/10 border-none">
                                    <OctagonAlertIcon className="h-4 w-4 text-destructive" />
                                    <AlertTitle>{error}</AlertTitle>
                                </Alert>
                            )}

                            <Button disabled={pending} type="submit" className="w-full bg-linear-to-r from-purple-400 to-pink-600">
                                Sign In
                            </Button>
                            {/* <div className="grid grid-rows-2 gap-4">
                                <Button
                                    disabled={pending}
                                    variant="outline"
                                    type="button"
                                    className="w-full flex items-center justify-center gap-3"
                                    onClick={() => onSocial('google')}
                                >
                                    <FaGoogle className="text-lg text-muted-foreground" />
                                    <span className="text-muted-foreground">Login with Google</span>
                                </Button>
                                <Button
                                    disabled={pending}
                                    variant="outline"
                                    type="button"
                                    className="w-full flex items-center justify-center gap-3"
                                    onClick={() => onSocial('github')}
                                >
                                    <FaGithub className="text-lg text-muted-foreground" />
                                    <span className="text-muted-foreground">Login with GitHub</span>
                                </Button>
                            </div> */}

                            <p className="text-center text-sm text-muted-foreground">
                                Don&apos;t have an account?{' '}
                                <Link href="/signup" className="underline text-blue-700">
                                    Sign Up
                                </Link>
                            </p>
                        </form>
                    </Form>
                </CardContent>
            </Card>

            <p className="text-center text-xs text-muted-foreground">
                By clicking continue, you agree to our{' '}
                <a href="#" className="underline hover:text-primary">Terms of Service</a>{' '}
                and{' '}
                <a href="#" className="underline hover:text-primary">Privacy Policy</a>.
            </p>
        </div>
    )
}
export default SignInView