import React from 'react';
import { Redirect, Tabs } from 'expo-router';
import { TabConfig } from '../config/TabConfig';
import { useFarm } from '../../src/offline/provider';
import { AlertScheduler } from '../../src/alerts/AlertScheduler';

export default function TabLayout() {
  const { farm } = useFarm();
  if (!farm?.zone_id) return <Redirect href="/ubicar" />;
  return (
    <>
      <AlertScheduler />
      <Tabs screenOptions={TabConfig.getOptions()}>{TabConfig.getScreens()}</Tabs>
    </>
  );
}
