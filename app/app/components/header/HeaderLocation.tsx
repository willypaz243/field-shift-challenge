import React from 'react';
import { Text } from 'react-native';
import { useOffline, useOfflineReady } from '../../../src/offline/provider';
import { headerLine } from '../../../src/ui/header-line';

type Props = { style: object };

function SyncedLocation({ style }: Props) {
  const { data, updatedAt } = useOffline();
  const zone = data?.zone as { nombre?: string } | undefined;
  const name = zone?.nombre?.split(' (')[0] ?? null;
  return <Text style={style}>{headerLine(name, updatedAt)}</Text>;
}

export function HeaderLocation({ style }: Props) {
  if (!useOfflineReady()) return <Text style={style}>{headerLine(null, null)}</Text>;
  return <SyncedLocation style={style} />;
}
