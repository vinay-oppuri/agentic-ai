'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import Image from 'next/image';

const Header = () => {

  const headers = [
    { label: "Home", href: "/" },
    { label: "Features", href: "#features" },
    { label: "About", href: "/about" },
    { label: "FAQ", href: "#faq" },
  ]
  return (
    <header className="sticky top-0 z-50 flex flex-row justify-between items-center text-sm backdrop-blur-sm px-30 py-4">
      <div className='flex gap-2 items-center'>
        <Image
          src="/Logo.svg"
          width={100}
          height={100}
          alt='Logo'
        />
      </div>
      <div className='flex flex-row font-semibold border-2 px-6 py-3 rounded-full gap-6 text-muted-foreground'>
        {headers.map((item) => (
          <Link key={item.href} href={item.href} className="text-foreground hover:scale-105 transition-transform duration-200">
            {item.label}
          </Link>
        ))}
      </div>
      <div>
        <Button className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold rounded-full transition-all duration-300 shadow-lg hover:shadow-purple-500/50">
          <Link href="/dashboard">Dashboard</Link>
        </Button>
      </div>
    </header>
  );
};

export default Header