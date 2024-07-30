export enum Element {
  MobileGoal = 0,
  RedRing = 1,
  BlueRing = 2,
}

export enum Direction {
  X = 0,
  Y = 1,
}

export interface Theme {
  id: string;
  componentBackground: string;
  font: string;
  control: string;
  controlHover: string;
}
