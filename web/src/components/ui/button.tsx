import { ButtonHTMLAttributes, cloneElement, forwardRef, isValidElement, ReactElement } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "outline" | "ghost";
  size?: "sm" | "md" | "lg";
  asChild?: boolean;
}

const baseStyles = "rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-violet-500";
const variantStyles = {
  default:
    "bg-violet-600 text-white hover:bg-violet-700 focus:ring-violet-500 dark:bg-violet-500 dark:text-white dark:hover:bg-violet-600",
  outline:
    "border border-zinc-300 bg-white text-zinc-700 hover:bg-zinc-50 hover:border-zinc-400 focus:ring-zinc-400 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-200 dark:hover:bg-zinc-700",
  ghost:
    "text-zinc-700 hover:bg-zinc-100 focus:ring-zinc-400 dark:text-zinc-300 dark:hover:bg-zinc-800",
};
const sizeStyles = {
  sm: "px-3 py-1.5 text-sm",
  md: "px-4 py-2 text-sm",
  lg: "px-6 py-3 text-base",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className = "", variant = "default", size = "md", asChild = false, children, ...props }, ref) => {
    const buttonClassName = `${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`;

    if (asChild && isValidElement(children)) {
      const { type: _type, ...restProps } = props;
      const child = children as ReactElement<{ className?: string }>;
      return cloneElement(child, {
        ...restProps,
        className: child.props.className ? `${buttonClassName} ${child.props.className}` : buttonClassName,
      });
    }

    return (
      <button
        ref={ref}
        className={buttonClassName}
        {...props}
        type={props.type ?? "button"}
      >
        {children}
      </button>
    );
  }
);
Button.displayName = "Button";
