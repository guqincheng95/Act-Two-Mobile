import type { CapacitorConfig } from '@capacitor/cli'

const config: CapacitorConfig = {
  appId: 'com.acttwomobile.app',
  appName: 'Act-Two Mobile',
  webDir: 'dist',
  server: {
    androidScheme: 'https',
  },
}

export default config
