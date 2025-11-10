"use client"

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { signUpFormSchema } from "@/db/schema";
import { signUp, signOut, useSession } from "@/lib/auth-client";
import { useState } from "react";
import { useForm } from "react-hook-form";
import z from "zod";
import { zodResolver } from '@hookform/resolvers/zod';
import { Card, CardContent } from "@/components/ui/card";
import Link from "next/link";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Alert, AlertTitle } from "@/components/ui/alert";
import { OctagonAlertIcon } from "lucide-react";


const SignUpView = () => {

    const [error, setError] = useState<string | null>(null)
    const [pending, setPending] = useState(false)

    const form = useForm<z.infer<typeof signUpFormSchema>>({
        resolver: zodResolver(signUpFormSchema),
        defaultValues: {
            name: "",
            email: "",
            password: "",
            confirmPassword: ""
        }
    })

    const onSubmit = (data: z.infer<typeof signUpFormSchema>) => {

        setPending(true)

        signUp.email({
            name: data.name,
            email: data.email,
            password: data.password,
            callbackURL: '/dashboard'
        }, {
            onSuccess: () => {
                setPending(false)
            },
            onError: ({ error }) => {
                setError(error.message)
            }
        })
    }

    return (
        <div className="flex flex-col items-center gap-6">
            <Card className="min-w-md overflow-hidden justify-center border-3 border-gray-900  bg-linear-to-br from-gray-900 to-black p-0">
                <CardContent className="grid p-0">
                    <Form {...form}>
                        <form onSubmit={form.handleSubmit(onSubmit)} className="p-6 md:p-8">
                            <div className="flex flex-col gap-6">
                                <div className="text-center">
                                    <h1 className="flex flex-col py-2 gap-4 text-3xl font-bold tracking-tighter bg-clip-text text-transparent bg-linear-to-r from-purple-400 to-pink-600">
                                        Let&apos;s get started
                                    </h1>
                                    <p className="text-muted-foreground">Create your account</p>
                                </div>

                                <FormField
                                    control={form.control}
                                    name="name"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>Name</FormLabel>
                                            <FormControl>
                                                <Input type="text" placeholder="Elon Musk" {...field} />
                                            </FormControl>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />
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
                                <FormField
                                    control={form.control}
                                    name="confirmPassword"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>Confirm Password</FormLabel>
                                            <FormControl>
                                                <Input type="password" placeholder="********" {...field} />
                                            </FormControl>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />

                                {!!error && (
                                    <Alert className="bg-destructive/10 border-none">
                                        <OctagonAlertIcon className="h-4 w-4 text-destructive!" />
                                        <AlertTitle>{error}</AlertTitle>
                                    </Alert>
                                )}

                                <Button disabled={pending} type="submit" className="w-full bg-linear-to-r from-purple-400 to-pink-600">
                                    Sign Up
                                </Button>

                                {/* <div className="grid grid-cols-2 gap-3">
                                    <Button
                                        disabled={pending}
                                        variant="outline"
                                        type="button"
                                        className="w-full flex items-center justify-center gap-2"
                                        onClick={() => onSocial("google")}
                                    >
                                        <FaGoogle className="text-lg" />
                                        <span className="hidden sm:inline">Google</span>
                                    </Button>
                                    <Button
                                        disabled={pending}
                                        variant="outline"
                                        type="button"
                                        className="w-full flex items-center justify-center gap-2"
                                        onClick={() => onSocial("github")}
                                    >
                                        <FaGithub className="text-lg" />
                                        <span className="hidden sm:inline">GitHub</span>
                                    </Button>
                                </div> */}

                                <div className="text-center text-sm">
                                    Already have an account?{" "}
                                    <Link href="/login" className="underline text-blue-600">
                                        Sign In
                                    </Link>
                                </div>
                            </div>
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

export default SignUpView