import type { IconProps as PhosphorIconProps } from "@phosphor-icons/react";
import {
  ChartBar,
  ClockCounterClockwise,
  ClipboardText,
  HouseLine,
  SignOut,
} from "@phosphor-icons/react";

type IconProps = PhosphorIconProps;

const defaultProps = {
  size: 22,
  weight: "duotone" as const,
};

export const ActiveOrdersIcon = (props: IconProps) => (
  <ChartBar {...defaultProps} {...props} />
);

export const OrderHistoryIcon = (props: IconProps) => (
  <ClockCounterClockwise {...defaultProps} {...props} />
);

export const MenuManagementIcon = (props: IconProps) => (
  <ClipboardText {...defaultProps} {...props} />
);

export const WaiterViewIcon = (props: IconProps) => (
  <HouseLine {...defaultProps} {...props} />
);

export const LogoutIcon = (props: IconProps) => (
  <SignOut {...defaultProps} {...props} />
);
