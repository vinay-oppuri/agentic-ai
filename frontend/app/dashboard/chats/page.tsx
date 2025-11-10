'use client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const ChatsPage = () => {
  return (
    <div className="grid flex-1 items-start gap-4 p-4 sm:px-6 sm:py-0 md:gap-8">
      <Card>
        <CardHeader>
          <CardTitle>Chats</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Chat functionality will be available soon.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default ChatsPage;
