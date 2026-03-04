---
name: react-native-architecture
description: >
  Build production React Native apps with Expo, navigation, native modules,
  offline sync, and cross-platform patterns. Use when starting a new mobile app,
  implementing navigation, integrating platform APIs, building offline-first
  features, optimizing RN performance, or setting up mobile CI/CD.
  Triggers: react native, expo, mobile app, react navigation, expo router,
  native module, offline first, react native performance, eas build,
  cross platform, ios, android, mobile architecture.
user-invokable: true
argument-hint: "<topic or feature>"
---

# React Native Architecture

Production patterns for React Native with Expo, covering project setup, navigation, state management, native integration, offline-first, performance, and CI/CD.

## When to Use

- Starting a new React Native or Expo project
- Implementing complex navigation patterns
- Integrating native modules and platform APIs
- Building offline-first mobile applications
- Optimizing React Native performance
- Setting up CI/CD for mobile releases

---

## Project Setup (Expo)

```bash
# Create new Expo project
npx create-expo-app@latest my-app --template tabs
cd my-app

# Or with blank TypeScript template
npx create-expo-app@latest my-app -t expo-template-blank-typescript
```

### Recommended Project Structure

```
src/
  app/                  # Expo Router file-based routes
    (tabs)/             # Tab navigator group
      index.tsx         # Home tab
      profile.tsx       # Profile tab
    _layout.tsx         # Root layout
    +not-found.tsx      # 404 screen
  components/           # Shared UI components
    ui/                 # Primitives (Button, Input, Card)
  hooks/                # Custom hooks
  lib/                  # Utilities, API client, storage
  store/                # State management (Zustand)
  constants/            # Theme, config, enums
  types/                # TypeScript definitions
```

---

## Navigation

### Expo Router (Recommended)

File-based routing, similar to Next.js.

```tsx
// app/_layout.tsx — Root layout
import { Stack } from 'expo-router';

export default function RootLayout() {
  return (
    <Stack>
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      <Stack.Screen name="modal" options={{ presentation: 'modal' }} />
    </Stack>
  );
}

// app/(tabs)/_layout.tsx — Tab navigator
import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

export default function TabLayout() {
  return (
    <Tabs>
      <Tabs.Screen
        name="index"
        options={{
          title: 'Home',
          tabBarIcon: ({ color }) => <Ionicons name="home" size={24} color={color} />,
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{ title: 'Profile' }}
      />
    </Tabs>
  );
}
```

### Navigation Patterns

| Pattern | Implementation |
|---------|---------------|
| **Stack** | `<Stack>` in layout — push/pop screens |
| **Tabs** | `<Tabs>` in layout — bottom tab bar |
| **Drawer** | `expo-router` with drawer layout |
| **Modal** | `presentation: 'modal'` in screen options |
| **Deep linking** | Automatic with Expo Router file paths |
| **Auth flow** | Conditional layout based on auth state |

### Auth-Protected Routes

```tsx
// app/_layout.tsx
import { Redirect } from 'expo-router';
import { useAuth } from '@/hooks/useAuth';

export default function RootLayout() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) return <SplashScreen />;
  if (!isAuthenticated) return <Redirect href="/login" />;

  return <Stack />;
}
```

---

## State Management

| Scope | Solution |
|-------|----------|
| **Component** | `useState`, `useReducer` |
| **Server data** | TanStack Query (React Query) |
| **Global UI** | Zustand |
| **Persistent** | MMKV + Zustand persist |
| **Forms** | React Hook Form |

### Zustand Store

```typescript
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { zustandStorage } from '@/lib/mmkv-storage';

interface AppStore {
  theme: 'light' | 'dark';
  setTheme: (theme: 'light' | 'dark') => void;
}

export const useAppStore = create<AppStore>()(
  persist(
    (set) => ({
      theme: 'light',
      setTheme: (theme) => set({ theme }),
    }),
    { name: 'app-store', storage: createJSONStorage(() => zustandStorage) }
  )
);
```

### TanStack Query for API Data

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

function useUser(id: string) {
  return useQuery({
    queryKey: ['user', id],
    queryFn: () => api.getUser(id),
    staleTime: 5 * 60 * 1000,
  });
}

function useUpdateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.updateUser,
    onSuccess: (_, vars) => qc.invalidateQueries({ queryKey: ['user', vars.id] }),
  });
}
```

---

## Native Modules & Platform APIs

### Using Expo Modules

```bash
npx expo install expo-camera expo-location expo-notifications expo-file-system
```

```typescript
import * as Location from 'expo-location';

async function getLocation() {
  const { status } = await Location.requestForegroundPermissionsAsync();
  if (status !== 'granted') throw new Error('Permission denied');
  return Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.High });
}
```

### Platform-Specific Code

```typescript
import { Platform } from 'react-native';

const styles = {
  shadow: Platform.select({
    ios: { shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1 },
    android: { elevation: 4 },
  }),
};

// File-based: MyComponent.ios.tsx / MyComponent.android.tsx
```

---

## Offline-First Architecture

### Storage Options

| Solution | Use For | Speed |
|----------|---------|-------|
| **MMKV** | Key-value, small data, preferences | Fastest |
| **SQLite (expo-sqlite)** | Structured data, queries, relations | Fast |
| **AsyncStorage** | Legacy key-value (avoid for new) | Slow |
| **FileSystem** | Large files, downloads, cache | Varies |

### Offline Queue Pattern

```typescript
import NetInfo from '@react-native-community/netinfo';

class OfflineQueue {
  private queue: PendingAction[] = [];

  async enqueue(action: PendingAction) {
    this.queue.push(action);
    await this.persist();
    this.processIfOnline();
  }

  private async processIfOnline() {
    const { isConnected } = await NetInfo.fetch();
    if (!isConnected) return;

    while (this.queue.length > 0) {
      const action = this.queue[0];
      try {
        await this.execute(action);
        this.queue.shift();
        await this.persist();
      } catch {
        break; // Retry later
      }
    }
  }
}
```

---

## Performance

### Optimization Checklist

| Area | Action |
|------|--------|
| **Lists** | Use `FlashList` instead of `FlatList` |
| **Images** | Use `expo-image` (caching, blurhash, transitions) |
| **Animations** | Use `react-native-reanimated` (UI thread) |
| **Heavy computation** | Move to `worklet` or background thread |
| **Re-renders** | Profile with React DevTools, apply `memo` |
| **Bundle** | Use Hermes engine (default in Expo 49+) |
| **Startup** | Minimize root component, lazy load screens |

### FlashList (Drop-in FlatList Replacement)

```tsx
import { FlashList } from '@shopify/flash-list';

<FlashList
  data={items}
  renderItem={({ item }) => <ItemCard item={item} />}
  estimatedItemSize={80}
  keyExtractor={(item) => item.id}
/>
```

### Image Optimization

```tsx
import { Image } from 'expo-image';

<Image
  source={{ uri: imageUrl }}
  placeholder={{ blurhash: 'LKO2?U%2Tw=w]~RBVZRi};RPxuwH' }}
  contentFit="cover"
  transition={200}
  style={{ width: 200, height: 200 }}
/>
```

---

## CI/CD with EAS Build

### Setup

```bash
npm install -g eas-cli
eas login
eas build:configure
```

### eas.json

```json
{
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal"
    },
    "preview": {
      "distribution": "internal",
      "ios": { "simulator": true }
    },
    "production": {}
  },
  "submit": {
    "production": {
      "ios": { "appleId": "you@example.com", "ascAppId": "123456789" },
      "android": { "serviceAccountKeyPath": "./google-services.json" }
    }
  }
}
```

### Build Commands

```bash
eas build --platform ios --profile preview     # iOS simulator build
eas build --platform android --profile preview # Android APK
eas build --platform all --profile production  # Production builds
eas submit --platform all                       # Submit to stores
eas update --branch preview --message "Bug fix" # OTA update
```

---

## Project Checklist

- [ ] Expo SDK latest (or target version)
- [ ] TypeScript configured with strict mode
- [ ] Expo Router for navigation
- [ ] Zustand + MMKV for state persistence
- [ ] TanStack Query for server state
- [ ] FlashList for performant lists
- [ ] expo-image for optimized images
- [ ] Reanimated for animations
- [ ] EAS Build configured for CI/CD
- [ ] Deep linking tested
- [ ] Offline handling implemented
- [ ] Platform-specific code isolated
- [ ] Error boundaries at route level
