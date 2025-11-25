import React from "react";

interface IconProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  size?: number | string;
  weight?: "regular" | "bold" | "duotone" | "fill" | "light" | "thin";
}

export const UpiIcon = ({ size = 24, weight, style, ...props }: IconProps) => {
  return (
    <img
      src="/icons/upi.png"
      alt="UPI"
      style={{ width: size, height: size, objectFit: 'contain', ...style }}
      {...props}
    />
  );
};

export const CashIcon = ({ size = 24, weight, style, ...props }: IconProps) => {
  return (
    <img
      src="/icons/cash.png"
      alt="Cash"
      style={{ width: size, height: size, objectFit: 'contain', ...style }}
      {...props}
    />
  );
};

export const CardIcon = ({ size = 24, weight, style, ...props }: IconProps) => {
  return (
    <img
      src="/icons/card.png"
      alt="Card"
      style={{ width: size, height: size, objectFit: 'contain', ...style }}
      {...props}
    />
  );
};
