import { describe, expect, it } from 'vitest';

import { parseBBox, projectBBox } from './projectBBox';


describe('bounding-box projection', () => {
  it('projects the detector coordinates through cover cropping', () => {
    const result = projectBBox({
      box: [64, 48, 320, 240],
      frameWidth: 640,
      frameHeight: 480,
      containerWidth: 400,
      containerHeight: 400,
      fit: 'cover',
    });

    expect(result).not.toBeNull();
    expect(result?.left).toBeCloseTo(-13.333, 2);
    expect(result?.top).toBeCloseTo(40, 2);
    expect(result?.width).toBeCloseTo(213.333, 2);
    expect(result?.height).toBeCloseTo(160, 2);
  });

  it('mirrors browser coordinates against the exact processed frame', () => {
    const unmirrored = projectBBox({
      box: [50, 50, 150, 250],
      frameWidth: 400,
      frameHeight: 300,
      containerWidth: 400,
      containerHeight: 300,
    });
    const mirrored = projectBBox({
      box: [50, 50, 150, 250],
      frameWidth: 400,
      frameHeight: 300,
      containerWidth: 400,
      containerHeight: 300,
      mirrored: true,
    });

    expect(unmirrored).toEqual({ left: 50, top: 50, width: 100, height: 200 });
    expect(mirrored).toEqual({ left: 250, top: 50, width: 100, height: 200 });
  });

  it('rejects malformed boxes and clamps valid coordinates to frame bounds', () => {
    expect(parseBBox([1, 2, Number.NaN, 4])).toBeUndefined();
    expect(parseBBox([1, 2, 3])).toBeUndefined();
    expect(projectBBox({
      box: [-10, -20, 120, 80],
      frameWidth: 100,
      frameHeight: 100,
      containerWidth: 100,
      containerHeight: 100,
    })).toEqual({ left: 0, top: 0, width: 100, height: 80 });
    expect(projectBBox({
      box: [20, 20, 10, 10],
      frameWidth: 100,
      frameHeight: 100,
      containerWidth: 100,
      containerHeight: 100,
    })).toBeNull();
  });
});
