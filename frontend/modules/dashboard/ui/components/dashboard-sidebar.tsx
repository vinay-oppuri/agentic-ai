'use client';

import {
    Sidebar,
    SidebarContent,
    SidebarGroup,
    SidebarHeader,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
} from "@/components/ui/sidebar";
import { cn } from "@/lib/utils";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart, LayoutGrid, MessageCircle, Users } from "lucide-react";

const navitems = [
    {
        href: "/dashboard",
        title: "Dashboard",
        icon: LayoutGrid,
    },
    {
        href: "/dashboard/agents",
        title: "Agents",
        icon: Users,
    },
    {
        href: "/dashboard/chats",
        title: "Chats",
        icon: MessageCircle,
    },
    {
        href: "/dashboard/reports",
        title: "Reports",
        icon: BarChart,
    },
];

export function DashboardSidebar() {
    const pathname = usePathname();

    return (
        <Sidebar>
            <SidebarHeader>
                <Link href="/" className="flex items-center justify-center py-8">
                    <Image
                        src="/Logo.svg"
                        alt="Logo"
                        width={100}
                        height={100}
                    />
                </Link>
            </SidebarHeader>

            <SidebarContent>
                <SidebarGroup>
                    <SidebarMenu>
                        {navitems.map((item) => {
                            const Icon = item.icon;
                            const isActive = pathname === item.href;

                            return (
                                <SidebarMenuItem key={item.href}>
                                    <SidebarMenuButton
                                        tooltip={item.title}
                                        isActive={isActive}
                                        className={cn(
                                            "flex items-center gap-3 h-12 rounded-lg px-4 border border-transparent transition-all duration-300 hover:bg-purple-600/10 hover:text-purple-400 hover:scale-105",
                                            isActive && "bg-purple-600/10 text-purple-400 border-purple-600/20"
                                        )}
                                    >
                                        <Link href={item.href} className="flex items-center gap-3">
                                            <Icon className="h-5 w-5 shrink-0" />
                                            <span className="text-sm font-medium">{item.title}</span>
                                        </Link>
                                    </SidebarMenuButton>
                                </SidebarMenuItem>
                            );
                        })}
                    </SidebarMenu>
                </SidebarGroup>
            </SidebarContent>
        </Sidebar>
    );
}