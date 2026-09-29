import { Navigate, Route, Routes } from "react-router-dom";
import { ROUTES } from "../constants/routes";
import AppLayout from "../components/layout/AppLayout";
import ProtectedRoute from "./ProtectedRoute";
import Login from "../pages/auth/Login";
import Signup from "../pages/auth/Signup";
import VerifyEmail from "../pages/auth/VerifyEmail";
import VerifyPhone from "../pages/auth/VerifyPhone";
import Dashboard from "../pages/dashboard/Dashboard";
import SoilTest from "../pages/soil-test/SoilTest";
import SoilAnalyzer from "../pages/soil-test/SoilAnalyzer";
import UploadReport from "../pages/soil-test/UploadReport";
import Processing from "../pages/soil-test/Processing";
import VerifyData from "../pages/soil-test/VerifyData";
import SoilReport from "../pages/report/SoilReport";
import CropRecommendation from "../pages/recommendations/CropRecommendation";
import FertilizerRecommendation from "../pages/recommendations/FertilizerRecommendation";
import History from "../pages/history/History";
import CompareTests from "../pages/history/CompareTests";
import Assistant from "../pages/assistant/Assistant";
import Profile from "../pages/profile/Profile";
import GovernmentResources from "../pages/resources/GovernmentResources";
import DeveloperLogin from "../pages/developer/DeveloperLogin";
import DeveloperDashboard from "../pages/developer/DeveloperDashboard";
import AddScheme from "../pages/developer/AddScheme";
import DeveloperProtectedRoute from "./DeveloperProtectedRoute";
import ForgotPassword from "../pages/auth/ForgotPassword";
import ResetPassword from "../pages/auth/ResetPassword";
import Devices from "../pages/devices/Devices";

export default function AppRoutes(){
  return <Routes>
    <Route path={ROUTES.LOGIN} element={<Login/>}/>
    <Route path={ROUTES.SIGNUP} element={<Signup/>}/>
    <Route path={ROUTES.FORGOT_PASSWORD} element={<ForgotPassword/>}/>
    <Route path={ROUTES.RESET_PASSWORD} element={<ResetPassword/>}/>
    <Route path={ROUTES.VERIFY_EMAIL} element={<VerifyEmail/>}/>
    {/* VerifyPhone is kept as a standalone route for backwards compatibility
        but is no longer reachable from the signup/login flow. */}
    <Route path={ROUTES.VERIFY_PHONE} element={<VerifyPhone/>}/>
    <Route path={ROUTES.DEVELOPER_LOGIN} element={<DeveloperLogin/>}/>
    <Route element={<ProtectedRoute/>}>
      <Route element={<AppLayout/>}>
        <Route path={ROUTES.DASHBOARD} element={<Dashboard/>}/>
        <Route path={ROUTES.SOIL_TEST} element={<SoilTest/>}/>
        <Route path={ROUTES.SOIL_ANALYZER} element={<SoilAnalyzer/>}/>
        <Route path={ROUTES.UPLOAD_REPORT} element={<UploadReport/>}/>
        <Route path={ROUTES.PROCESSING} element={<Processing/>}/>
        <Route path={ROUTES.VERIFY_DATA} element={<VerifyData/>}/>
        <Route path={ROUTES.REPORT} element={<SoilReport/>}/>
        <Route path={ROUTES.CROPS} element={<CropRecommendation/>}/>
        <Route path={ROUTES.FERTILIZER} element={<FertilizerRecommendation/>}/>
        <Route path={ROUTES.HISTORY} element={<History/>}/>
        <Route path={ROUTES.COMPARE} element={<CompareTests/>}/>
        <Route path={ROUTES.ASSISTANT} element={<Assistant/>}/>
        <Route path={ROUTES.PROFILE} element={<Profile/>}/>
        <Route path={ROUTES.RESOURCES} element={<GovernmentResources/>}/>
        <Route path={ROUTES.DEVICES} element={<Devices/>}/>
      </Route>
    </Route>
    <Route element={<DeveloperProtectedRoute/>}>
      <Route path={ROUTES.DEVELOPER} element={<DeveloperDashboard/>}/>
      <Route path={ROUTES.DEVELOPER_ADD_SCHEME} element={<AddScheme/>}/>
    </Route>
    <Route path="*" element={<Navigate to={ROUTES.DASHBOARD} replace/>}/>
  </Routes>;
}
