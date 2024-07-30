import { Element } from "../lib/types";
import { images } from "./images";

/**
 * General configuration for the application
 */
export const config = {
  socketIP: "10.42.0.1",
  socketPort: "3030",

  /**
   * Default image width captured by the camera on the robot
   */
  SCALE_X: 640,

  /**
   * Default image height captured by the camera on the robot
   */
  SCALE_Y: 480,

  /**
   * Rate at which the data services polls for data (ms)
   */
  pollingInterval: 60,
  logDataResponse: false,
  detectOutOfBoundsElements: true,
  colors: {
    red: "#D22630",
    darkRed: "#971c22",
    gray: "#939597",
    darkGray: "#58585B",
    darkerGray: "#111111",
    blue: "#0077C8",
    darkBlue: "#004d80",
    black: "#000000",
    white: "#F4F2FF",
    orange: "#fca503",
    darkOrange: "#bf7e04",
    purple: "#7466F1",
    darkPurple: "#433b87",
    grayPurple: "#293045",
  },
  field: {
    dimension: 3.6576, // meters
    oov: 0.1,
    texture: images.field,
    compass: {
      texture: images.map.compass,
      scale: 0.23,
      ringPositionCorrectionX: 0.1,
      lineScale: 0.03,
      numberOffset: 0.045,
      numberScale: 0.017,
    },
    fog: {
      opacity: 0.75,
    },
    ruler: {
      texture: images.map.ruler,
      xySidebarOffset: 0.26,
      xySidebarMarkersOffset: 0.22,
      xySidebarArrowOffset: 0.22,
      xySidebarSizeMultiplier: 0.025,
      arrowScale: 0.1,
    },
    robot: {
      length: 0.47, // meters
      width: 0.444, // meters
      texture: images.robot,
      textureWidth: 497, // pixels
      textureHeight: 589, // pixels
      fov: 50,
    },
  },
  elements: {
    textures: {
      [Element.MobileGoal]: images.elements.mobileGoal,
      [Element.RedRing]: images.elements.redRing,
      [Element.BlueRing]: images.elements.blueRing,
    },
    scale: {
      [Element.MobileGoal]: 0.1,
      [Element.RedRing]: 0.078,
      [Element.BlueRing]: 0.078,
    },
    borderColors: {
      [Element.MobileGoal]: "rgba(0, 255, 0, .8)",
      [Element.RedRing]: "rgba(255, 0, 0, .8)",
      [Element.BlueRing]: "rgba(0, 0, 255, .8)",
    },
    backgroundColors: {
      [Element.MobileGoal]: "rgba(0, 255, 0, .3)",
      [Element.RedRing]: "rgba(255, 0, 0, .3)",
      [Element.BlueRing]: "rgba(0, 0, 255, .3)",
    },
    label: {
      textColors: {
        white: "rgba(255, 255, 255, 1)",
        black: "rgba(0, 0, 0, 1)",
      },
      text: {
        [Element.MobileGoal]: "Mobile Goal",
        [Element.RedRing]: "Red Ring",
        [Element.BlueRing]: "Blue Ring",
      },
    },
  },
};
