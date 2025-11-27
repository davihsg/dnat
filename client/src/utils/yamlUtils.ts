/**
 * Convert an object to YAML format (simplified implementation)
 * For production, consider using a library like 'js-yaml'
 */
export function objectToYAML(obj: Record<string, any>, indent = 0): string {
  const indentStr = "  ".repeat(indent);
  let yaml = "";

  for (const [key, value] of Object.entries(obj)) {
    if (value === null || value === undefined) {
      continue;
    }

    if (typeof value === "object" && !Array.isArray(value)) {
      yaml += `${indentStr}${key}:\n${objectToYAML(value, indent + 1)}`;
    } else if (Array.isArray(value)) {
      yaml += `${indentStr}${key}:\n`;
      value.forEach((item) => {
        if (typeof item === "object") {
          yaml += `${indentStr}  -\n${objectToYAML(item, indent + 2)}`;
        } else {
          yaml += `${indentStr}  - ${formatYAMLValue(item)}\n`;
        }
      });
    } else {
      yaml += `${indentStr}${key}: ${formatYAMLValue(value)}\n`;
    }
  }

  return yaml;
}

function formatYAMLValue(value: any): string {
  if (typeof value === "string") {
    // Escape special characters and wrap in quotes if needed
    if (value.includes(":") || value.includes("\n") || value.includes('"')) {
      return `"${value.replace(/"/g, '\\"')}"`;
    }
    return value;
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return String(value);
}

