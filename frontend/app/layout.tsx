import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'FlightVault - Visual Disaster Recovery',
  description: 'Git for your database using MariaDB System-Versioned Tables',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}