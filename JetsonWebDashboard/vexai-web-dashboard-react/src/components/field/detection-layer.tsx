import React from "react";
import { Layer, Image } from "react-konva";
import { config } from "../../util/config";
import { useAppSelector } from "../../state/hooks";
import { Element } from "../../lib/types";
import { v4 as uuidv4 } from "uuid";
import useImage from "use-image";

interface DetectionLayerProps {
  fieldWidth: number;
  fieldHeight: number;
}

/**
 * Displays elements on the field detected by the robot
 *
 * @param param0 Detection layer properties
 * @returns JSX.Element
 */
const DetectionLayer = ({ fieldWidth, fieldHeight }: DetectionLayerProps) => {
  const detections = useAppSelector((state) => state.data.response.detections);
  const scale = useAppSelector((state) => state.app.scale);
  const [mobileGoal] = useImage(
    config.elements.textures[Element.MobileGoal]
  );
  const [redPickup] = useImage(config.elements.textures[Element.RedRing]);
  const [bluePickup] = useImage(config.elements.textures[Element.BlueRing]);

  const getImage = (detectionClass: number) => {
    switch (detectionClass) {
      case Element.MobileGoal:
        return mobileGoal;
      case Element.RedRing:
        return redPickup;
      case Element.BlueRing:
        return bluePickup;
      default:
        break;
    }
  };

  return (
    <Layer>
      {detections ? (
        <>
          {detections.map((detection) => {
            return (
              <>
                {detection.depth !== -1 ? (
                  <Image
                    key={`${
                      config.elements.label.text[detection.class]
                    }-${uuidv4()}`}
                    alt=""
                    image={getImage(detection.class)}
                    x={detection.mapLocation.x[0] * scale}
                    y={detection.mapLocation.y[0] * scale * -1}
                    z={detection.depth}
                    width={
                      config.elements.scale[detection.class] *
                      (fieldWidth +
                        config.elements.scale[detection.class] * 5 * fieldWidth)
                    }
                    height={
                      config.elements.scale[detection.class] * fieldHeight
                    }
                    offsetX={
                      (config.elements.scale[detection.class] *
                        (fieldWidth +
                          config.elements.scale[detection.class] *
                            5 *
                            fieldWidth)) /
                      2
                    }
                    offsetY={
                      (config.elements.scale[detection.class] * fieldHeight) /
                      2.5
                    }
                  />
                ) : null}
              </>
            );
          })}
        </>
      ) : null}
    </Layer>
  );
};

export default DetectionLayer;
