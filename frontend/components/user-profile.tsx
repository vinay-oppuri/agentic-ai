'use client';

import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { signOut } from '@/lib/auth-client';
import { ChevronDown } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

const UserProfile = () => {
  const router = useRouter();

  const onSubmit = async () => {
    await signOut({
      fetchOptions: {
        onSuccess: () => {
          router.push("/login");
        },
      },
    });

  }
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <div className='flex items-center justify-center gap-2'>
          <Avatar className="cursor-pointer">
            <AvatarImage
              src="https://github.com/shadcn.png"
              alt="User"
            />
            <AvatarFallback>U</AvatarFallback>
          </Avatar>
          <ChevronDown size="20" />
        </div>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="bg-black/80 backdrop-blur-lg border-white/20 text-white">
        <DropdownMenuLabel>My Account</DropdownMenuLabel>
        <DropdownMenuSeparator className="bg-white/20" />
        <DropdownMenuItem>Profile</DropdownMenuItem>
        <DropdownMenuItem>Settings</DropdownMenuItem>
        <DropdownMenuSeparator className="bg-white/20" />
        <DropdownMenuItem onClick={() => onSubmit()}>Logout</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default UserProfile;