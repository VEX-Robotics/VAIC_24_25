import React, { useEffect } from "react";
import {
  setDataService,
  setDataServiceConnected,
  updateResponse,
} from "./state/data-slice";
import "./App.css";
import { useAppDispatch, useAppSelector } from "./state/hooks";
import Navigator from "./components/navigation/navigator";
import { DataService } from "./services/data-service";
import { Offset, DataResponse, ColorCorrection } from "./lib/data-response";
import { setCameraOffset, setGpsOffset, setColorCorrection } from "./state/settings-slice";

/**
 * App
 *
 * @returns JSX.Element
 */
const App = () => {
  const dispatch = useAppDispatch();
  const socketIp = useAppSelector((state) => state.settings.socketIp);
  const socketPort = useAppSelector((state) => state.settings.socketPort);

  useEffect(() => {
    const dataService = new DataService(socketIp, socketPort);
    dispatch(setDataService(dataService));

    dataService.on("socketConnected", () => {
      dispatch(setDataServiceConnected(true));
      dataService.getCameraOffset();
      dataService.getGpsOffset();
      dataService.getColorCorrection();
    });

    dataService.on("message", (msg: DataResponse) => {
      dispatch(updateResponse(msg));
    });

    dataService.on("getCameraOffset", (msg: Offset) => {
      dispatch(setCameraOffset(msg));
    });

    dataService.on("getGpsOffset", (msg: Offset) => {
      dispatch(setGpsOffset(msg));
    });

    dataService.on("getColorCorrection", (msg: ColorCorrection) => {
      dispatch(setColorCorrection(msg));
    });

    dataService.on("socketConnectionClosed", () => {
      dispatch(setDataServiceConnected(false));
    });
  }, []);

  return (
    <>
      <Navigator />
    </>
  );
};

export default App;
