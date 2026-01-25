import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
    title: 'SOS 42 - PDF Document Assistant',
    description: 'The adulting companion for students - Ask questions about your PDFs',
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en">
            <body className="antialiased">{children}</body>
        </html>
    );
}