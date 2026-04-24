import { Player } from '@lottiefiles/react-lottie-player';
import loadingAnimation from './loading.json';

export default function LoadingSpinner() {
  return (
    <div className="flex justify-center items-center min-h-screen">
      <Player
        autoplay
        loop
        src={loadingAnimation}
        style={{ height: '200px', width: '200px' }}
      />
    </div>
  );
}
