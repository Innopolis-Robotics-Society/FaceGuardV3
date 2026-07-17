import { describe, expect, it } from 'vitest';
import { parseBBox, projectBBox } from './projectBBox';

describe('projectBBox', () => {
  it('projects and mirrors a matching 16:9 frame', () => {
    const normal = projectBBox({
      box: [128, 72, 384, 216],
      frameWidth: 1280,
      frameHeight: 720,
      containerWidth: 800,
      containerHeight: 450,
    });
    const mirrored = projectBBox({
      box: [128, 72, 384, 216],
      frameWidth: 1280,
      frameHeight: 720,
      containerWidth: 800,
      containerHeight: 450,
      mirrored: true,
    });

    expect(normal).toEqual({ left: 80, top: 45, width: 160, height: 90 });
    expect(mirrored).toEqual({ left: 560, top: 45, width: 160, height: 90 });
  });

  it('accounts for centered cropping with object-fit cover', () => {
    expect(projectBBox({
      box: [64, 96, 192, 240],
      frameWidth: 640,
      frameHeight: 480,
      containerWidth: 800,
      containerHeight: 450,
      fit: 'cover',
    })).toEqual({ left: 80, top: 45, width: 160, height: 180 });
  });

  it('accounts for letterboxing with object-fit contain', () => {
    expect(projectBBox({
      box: [64, 48, 192, 144],
      frameWidth: 640,
      frameHeight: 480,
      containerWidth: 800,
      containerHeight: 450,
      fit: 'contain',
    })).toEqual({ left: 160, top: 45, width: 120, height: 90 });
  });

  it('clamps coordinates and rejects invalid input', () => {
    expect(projectBBox({
      box: [-10, -20, 700, 500],
      frameWidth: 640,
      frameHeight: 480,
      containerWidth: 640,
      containerHeight: 480,
    })).toEqual({ left: 0, top: 0, width: 640, height: 480 });
    expect(projectBBox({
      box: [1, 1, 2, 2],
      frameWidth: 0,
      frameHeight: 480,
      containerWidth: 640,
      containerHeight: 480,
    })).toBeNull();
    expect(parseBBox([1, 2, 3])).toBeUndefined();
    expect(parseBBox([1, 2, Number.NaN, 4])).toBeUndefined();
  });
});
