'use client';

import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import Header from '@/components/Header';
import Footer from '@/components/Footer';

export default function ClientRootLayout({ children }) {
  const pathname = usePathname();
  const [showHeader, setShowHeader] = useState(true);
  const [showFooter, setShowFooter] = useState(true);

  useEffect(() => {
    // Ẩn Header và Footer nếu đường dẫn bắt đầu với /auth
    if (pathname.startsWith('/auth')) {
      setShowHeader(false);
      setShowFooter(false);
    } 
    // Ẩn Footer nhưng giữ Header cho /manage
    else if (pathname.startsWith('/manage')) {
      setShowHeader(true);
      setShowFooter(false);
    } 
    // Hiển thị cả Header và Footer cho các trang khác
    else {
      setShowHeader(true);
      setShowFooter(true);
    }
  }, [pathname]);

  return (
    <>
      {showHeader && <Header />}
      {children}
      {showFooter && <Footer />}
    </>
  );
}
