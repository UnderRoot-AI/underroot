import { Navigate, Outlet } from "react-router-dom";
import Loading from "../components/common/Loading";
import { useAuth } from "../hooks/useAuth";
import { ROUTES } from "../constants/routes";

export default function ProtectedRoute(){
  const {user,loading}=useAuth();
  if(loading)return <Loading label="Checking your session..."/>;
  return user?<Outlet/>:<Navigate to={ROUTES.LOGIN} replace/>;
}
