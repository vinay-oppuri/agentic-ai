'use client';

import { PanelLeft, Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { useSidebar } from '@/components/ui/sidebar';
import { Button } from '@/components/ui/button';
import UserProfile from '@/components/user-profile';

const DashboardNavbar = () => {
  const { toggleSidebar } = useSidebar();

  return (
    <header className="sticky top-0 z-50 flex h-18 items-center gap-4 px-4 backdrop-blur-lg">
      <Button
        variant="ghost"
        size="icon-lg"
        onClick={toggleSidebar}
        className="shrink-0"
        aria-label="Toggle sidebar"
      >
        <PanelLeft className="h-5 w-5" />
      </Button>

      <div className="flex-1">
        <form className="w-full">
          <div className="relative w-full">
            <Search className="absolute left-2.5 top-3 h-4 w-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search..."
              className="w-full h-10 pl-9 border-none bg-muted/30"
            />
          </div>
        </form>
      </div>

      <UserProfile />
    </header>
  );
};

export default DashboardNavbar;