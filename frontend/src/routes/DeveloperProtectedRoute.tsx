import { Navigate, Outlet } from "react-router-dom";
import { ROUTES } from "../constants/routes";
export default function DeveloperProtectedRoute(){ return localStorage.getItem("developer_token") ? <Outlet/> : <Navigate to={ROUTES.DEVELOPER_LOGIN} replace/>; }
