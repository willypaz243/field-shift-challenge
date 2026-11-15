import type { ReactNode } from "react";
import {
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { Colors, Radius, Typography } from "../../constants/Theme";

type Props = {
  visible: boolean;
  title: string;
  subtitle?: string;
  closeLabel: string;
  onClose: () => void;
  children: ReactNode;
  // A required question (the harvest one) closes only by answering.
  dismissable?: boolean;
};

export function Sheet({
  visible,
  title,
  subtitle,
  closeLabel,
  onClose,
  children,
  dismissable = true,
}: Props) {
  return (
    <Modal
      visible={visible}
      transparent
      animationType="slide"
      onRequestClose={dismissable ? onClose : () => undefined}
    >
      {dismissable ? (
        <Pressable
          style={styles.backdrop}
          onPress={onClose}
          accessibilityLabel={closeLabel}
        />
      ) : (
        <View style={styles.backdrop} />
      )}
      <View style={styles.sheet}>
        <View style={styles.grab} />
        <View style={styles.head}>
          <View style={{ flex: 1 }}>
            <Text style={styles.title}>{title}</Text>
            {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
          </View>
          {dismissable && (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={closeLabel}
              onPress={onClose}
              style={styles.close}
            >
              <Text style={styles.closeText}>×</Text>
            </Pressable>
          )}
        </View>
        <ScrollView contentContainerStyle={styles.body}>{children}</ScrollView>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, backgroundColor: "rgba(10,20,14,0.45)" },
  sheet: {
    maxHeight: "88%",
    backgroundColor: Colors.paper,
    borderTopLeftRadius: Radius.sheet,
    borderTopRightRadius: Radius.sheet,
  },
  grab: {
    width: 48,
    height: 5,
    borderRadius: 3,
    backgroundColor: Colors.line,
    alignSelf: "center",
    marginTop: 10,
    marginBottom: 4,
  },
  head: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    paddingHorizontal: 18,
    paddingTop: 6,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.line,
  },
  title: { ...Typography.headline, color: Colors.ink },
  subtitle: { ...Typography.label, color: Colors.ink2 },
  close: {
    width: 56,
    height: 56,
    alignItems: "center",
    justifyContent: "center",
  },
  closeText: { fontSize: 32, color: Colors.ink2 },
  body: { padding: 16, gap: 8, paddingBottom: 40 },
});
