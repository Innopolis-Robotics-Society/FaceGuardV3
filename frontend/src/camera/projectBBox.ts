export type BBox = [number, number, number, number];
export type ObjectFit = 'cover' | 'contain';

export interface BBoxProjectionInput {
  box: BBox;
  frameWidth: number;
  frameHeight: number;
  containerWidth: number;
  containerHeight: number;
  fit?: ObjectFit;
  mirrored?: boolean;
}

export interface ProjectedBBox {
  left: number;
  top: number;
  width: number;
  height: number;
}

function isPositiveFinite(value: number) {
  return Number.isFinite(value) && value > 0;
}

export function parseBBox(value: unknown): BBox | undefined {
  if (!Array.isArray(value) || value.length !== 4) return undefined;
  if (!value.every(item => typeof item === 'number' && Number.isFinite(item))) {
    return undefined;
  }
  return [value[0], value[1], value[2], value[3]];
}

export function projectBBox({
  box,
  frameWidth,
  frameHeight,
  containerWidth,
  containerHeight,
  fit = 'cover',
  mirrored = false,
}: BBoxProjectionInput): ProjectedBBox | null {
  if (
    !isPositiveFinite(frameWidth) ||
    !isPositiveFinite(frameHeight) ||
    !isPositiveFinite(containerWidth) ||
    !isPositiveFinite(containerHeight) ||
    !box.every(Number.isFinite)
  ) {
    return null;
  }

  const x1 = Math.min(frameWidth, Math.max(0, box[0]));
  const y1 = Math.min(frameHeight, Math.max(0, box[1]));
  const x2 = Math.min(frameWidth, Math.max(0, box[2]));
  const y2 = Math.min(frameHeight, Math.max(0, box[3]));
  if (x2 <= x1 || y2 <= y1) return null;

  const scaleX = containerWidth / frameWidth;
  const scaleY = containerHeight / frameHeight;
  const scale = fit === 'contain' ? Math.min(scaleX, scaleY) : Math.max(scaleX, scaleY);
  const offsetX = (containerWidth - frameWidth * scale) / 2;
  const offsetY = (containerHeight - frameHeight * scale) / 2;
  const unmirroredLeft = offsetX + x1 * scale;
  const unmirroredRight = offsetX + x2 * scale;

  return {
    left: mirrored ? containerWidth - unmirroredRight : unmirroredLeft,
    top: offsetY + y1 * scale,
    width: (x2 - x1) * scale,
    height: (y2 - y1) * scale,
  };
}
