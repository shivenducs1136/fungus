import { useEffect, useRef } from 'react';

export const ParticlesBackground = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width: number;
    let height: number;
    let particles: Array<{ x: number; y: number; radius: number; vx: number; vy: number; opacity: number }> = [];
    let animationFrameId: number;

    const initParticles = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
      particles = [];
      const particleCount = Math.floor((width * height) / 18000);

      for (let i = 0; i < particleCount; i++) {
        particles.push({
          x: Math.random() * width,
          y: Math.random() * height,
          radius: Math.random() * 1.5 + 0.5,
          vx: Math.random() * 0.25 + 0.05,
          vy: -(Math.random() * 0.25 + 0.05),
          opacity: Math.random() * 0.25 + 0.05,
        });
      }
    };

    const animateParticles = () => {
      ctx.clearRect(0, 0, width, height);

      particles.forEach((p) => {
        p.x += p.vx;
        p.y += p.vy;

        if (p.x > width + 5) p.x = -5;
        if (p.y < -5) p.y = height + 5;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(38, 34, 26, ${p.opacity})`;
        ctx.fill();
      });

      animationFrameId = requestAnimationFrame(animateParticles);
    };

    window.addEventListener('resize', initParticles);
    initParticles();
    animateParticles();

    return () => {
      window.removeEventListener('resize', initParticles);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        zIndex: -1,
        pointerEvents: 'none',
      }}
    />
  );
};
