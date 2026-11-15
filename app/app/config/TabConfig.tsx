import React from 'react';
import { Tabs } from 'expo-router';
import { GlobalHeader } from '../components/header/GlobalHeader';
import { TabIcon } from '../components/tabs/TabIcon';
import { Colors } from '../../constants/Theme';

export class TabConfig {
  static getOptions(): any {
    const style = { height: 80, paddingBottom: 12, paddingTop: 8, backgroundColor: Colors.paper, borderTopColor: Colors.line };
    const label = { fontSize: 17, fontFamily: 'AtkinsonHyperlegibleNext-Bold', marginTop: 4 };
    return { header: () => <GlobalHeader />, tabBarActiveTintColor: Colors.fieldDeep, 
             tabBarInactiveTintColor: Colors.ink2, tabBarStyle: style, tabBarLabelStyle: label, 
             tabBarItemStyle: { minHeight: 56 } };
  }

  static getScreens() {
    return [ this.buildScreen("index", "Hoy", "home"),
             this.buildScreen("calendario", "Calendario", "calendar"),
             this.buildScreen("sembrar", "Sembrar", "sprout", true),
             this.buildScreen("mizona", "Mi zona", "map") ];
  }

  private static buildScreen(name: string, title: string, icon: string, isMat = false) {
    return <Tabs.Screen key={name} name={name} options={{ title, tabBarIcon: ({ focused, color }: any) => <TabIcon name={icon} isMaterial={isMat} focused={focused} color={color} /> }} />;
    
  }
}